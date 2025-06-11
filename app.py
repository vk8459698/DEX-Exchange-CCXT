import ccxt
import asyncio
from web3 import Web3
from web3.middleware import geth_poa_middleware
from decimal import Decimal
import json
from typing import Dict, List, Optional, Any
import time

class DEXExchange(ccxt.Exchange):
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        
        super().__init__(config)
        
        self.id = 'dex'
        self.name = 'Custom DEX'
        self.version = '1.0'
        self.rateLimit = 1000
        
        # Web3 setup
        rpc_url = config.get('rpcUrl', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Add middleware for PoA chains if needed
        if config.get('poa', False):
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Wallet setup
        self.private_key = config.get('privateKey')
        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
            self.address = self.account.address
        else:
            self.account = None
            self.address = None
        
        # Common DEX contract addresses
        self.contracts = {
            'uniswap_v2_router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            'uniswap_v3_router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
            'sushiswap_router': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
            'pancakeswap_router': '0x10ED43C718714eb63d5aA57B78B54704E256024E',  # BSC
        }
        
        # ERC20 ABI
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }
        ]
        
        # Uniswap V2 Router ABI (simplified)
        self.router_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"name": "amounts", "type": "uint256[]"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForTokens",
                "outputs": [{"name": "amounts", "type": "uint256[]"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                    {"name": "amountADesired", "type": "uint256"},
                    {"name": "amountBDesired", "type": "uint256"},
                    {"name": "amountAMin", "type": "uint256"},
                    {"name": "amountBMin", "type": "uint256"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "name": "addLiquidity",
                "outputs": [
                    {"name": "amountA", "type": "uint256"},
                    {"name": "amountB", "type": "uint256"},
                    {"name": "liquidity", "type": "uint256"}
                ],
                "type": "function"
            }
        ]
        
        # Cache for positions and approvals
        self.positions_cache = {}
        self.approvals_cache = {}
        
        # Common token addresses (mainnet)
        self.common_tokens = {
    'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # Correct USDC
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
}

    # DeFi Positions Management
    def fetch_positions(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch DeFi positions for the connected wallet"""
        if not self.address:
            raise ValueError("Wallet not configured")
        
        try:
            positions = []
            tokens_to_check = symbols or list(self.common_tokens.values())
            
            for token_address in tokens_to_check:
                try:
                    position = self.get_token_position(self.address, token_address)
                    if position['balance'] > 0:
                        positions.append(position)
                except Exception as e:
                    print(f"Error fetching position for {token_address}: {e}")
                    continue
            
            # Cache positions
            self.positions_cache[self.address] = positions
            
            return positions
        except Exception as e:
            raise Exception(f"Failed to fetch positions: {str(e)}")
    
    def get_token_position(self, address: str, token_address: str) -> Dict[str, Any]:
        """Get detailed position for a specific token"""
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi
        )
        
        try:
            # Get token info
            balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
            decimals = contract.functions.decimals().call()
            symbol = contract.functions.symbol().call()
            name = contract.functions.name().call()
            
            # Format balance
            formatted_balance = balance / (10 ** decimals)
            
            return {
                'symbol': symbol,
                'name': name,
                'address': token_address,
                'balance': formatted_balance,
                'raw_balance': str(balance),
                'decimals': decimals,
                'timestamp': int(time.time())
            }
        except Exception as e:
            raise Exception(f"Failed to get token position: {str(e)}")
    
    def get_liquidity_positions(self, address: str) -> List[Dict[str, Any]]:
        """Get liquidity provider positions"""
        # This would involve checking LP token balances
        # Implementation depends on specific DEX protocols
        lp_positions = []
        
        # Example: Check Uniswap V2 LP tokens
        # You would need to implement pair discovery and LP token checking
        
        return lp_positions
    
    def get_staking_positions(self, address: str) -> List[Dict[str, Any]]:
        """Get staking positions"""
        # Implementation for various staking contracts
        staking_positions = []
        
        return staking_positions

    # Token Approvals Management
    def fetch_approvals(self, token_address: str, spender_address: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch token approvals for DEX routers"""
        if not self.address:
            raise ValueError("Wallet not configured")
        
        try:
            approvals = []
            
            if spender_address:
                # Check specific spender
                approval = self.get_token_approval(self.address, token_address, spender_address)
                approvals.append(approval)
            else:
                # Check all common DEX routers
                for name, router_address in self.contracts.items():
                    try:
                        approval = self.get_token_approval(self.address, token_address, router_address)
                        approval['spender_name'] = name
                        approvals.append(approval)
                    except Exception as e:
                        print(f"Error checking approval for {name}: {e}")
                        continue
            
            # Cache approvals
            cache_key = f"{token_address}_{self.address}"
            self.approvals_cache[cache_key] = approvals
            
            return approvals
        except Exception as e:
            raise Exception(f"Failed to fetch approvals: {str(e)}")
    
    def get_token_approval(self, owner_address: str, token_address: str, spender_address: str) -> Dict[str, Any]:
        """Get specific token approval amount"""
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=self.erc20_abi
        )
        
        try:
            allowance = contract.functions.allowance(
                Web3.to_checksum_address(owner_address),
                Web3.to_checksum_address(spender_address)
            ).call()
            
            decimals = contract.functions.decimals().call()
            symbol = contract.functions.symbol().call()
            
            # Check if unlimited approval
            max_uint256 = 2**256 - 1
            is_unlimited = allowance >= max_uint256 // 2  # Close to max uint256
            
            return {
                'token': symbol,
                'token_address': token_address,
                'spender': spender_address,
                'allowance': allowance / (10 ** decimals),
                'raw_allowance': str(allowance),
                'decimals': decimals,
                'is_unlimited': is_unlimited,
                'timestamp': int(time.time())
            }
        except Exception as e:
            raise Exception(f"Failed to get token approval: {str(e)}")
    
    def approve_token(self, token_address: str, spender_address: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Approve token for spending"""
        if not self.account:
            raise ValueError("Private key not configured")
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.erc20_abi
            )
            
            # Get token decimals
            decimals = contract.functions.decimals().call()
            symbol = contract.functions.symbol().call()
            
            # Set approval amount
            if amount is None:
                # Unlimited approval
                approval_amount = 2**256 - 1
                amount_str = "unlimited"
            else:
                approval_amount = int(amount * (10 ** decimals))
                amount_str = str(amount)
            
            # Build transaction
            tx = contract.functions.approve(
                Web3.to_checksum_address(spender_address),
                approval_amount
            ).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address)
            })
            
            # Sign and send transaction
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': receipt['status'] == 1,
                'tx_hash': tx_hash.hex(),
                'amount': amount_str,
                'token': symbol,
                'spender': spender_address,
                'gas_used': receipt['gasUsed']
            }
        except Exception as e:
            raise Exception(f"Failed to approve token: {str(e)}")
    
    def revoke_approval(self, token_address: str, spender_address: str) -> Dict[str, Any]:
        """Revoke token approval"""
        return self.approve_token(token_address, spender_address, 0)

    # Utility Functions
    def get_wallet_tokens(self, address: str) -> List[str]:
        """Get list of tokens in wallet (simplified)"""
        # In practice, you'd scan blockchain for token transfers
        return list(self.common_tokens.values())
    
    def get_token_price(self, token_address: str) -> float:
        """Get token price (would integrate with price oracles)"""
        # Implementation would query DEX for prices or use price oracles
        return 0.0

    # CCXT Override Methods
    def load_markets(self, reload: bool = False, params: Dict = None) -> Dict:
        """Load available markets from DEX"""
        if params is None:
            params = {}
        
        # Implementation would discover trading pairs from DEX
        self.markets = {}
        return self.markets
    
    def fetch_balance(self, params: Dict = None) -> Dict[str, Any]:
        """Fetch wallet balance in CCXT format"""
        if params is None:
            params = {}
        
        positions = self.fetch_positions()
        balance = {}
        
        for position in positions:
            balance[position['symbol']] = {
                'free': position['balance'],
                'used': 0,
                'total': position['balance']
            }
        
        return balance

    # DEX Trading Functions
    def create_order(self, symbol: str, type: str, side: str, amount: float, 
                    price: Optional[float] = None, params: Dict = None) -> Dict[str, Any]:
        """Create order on DEX"""
        if params is None:
            params = {}
        
        # Implementation for DEX swaps
        raise NotImplementedError("DEX trading implementation needed")
    
    def add_liquidity(self, token_a: str, token_b: str, amount_a: float, 
                     amount_b: float, params: Dict = None) -> Dict[str, Any]:
        """Add liquidity to DEX pool"""
        if params is None:
            params = {}
        
        if not self.account:
            raise ValueError("Private key not configured")
        
        try:
            router_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contracts['uniswap_v2_router']),
                abi=self.router_abi
            )
            
            # Get token contracts for decimals
            token_a_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_a),
                abi=self.erc20_abi
            )
            token_b_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_b),
                abi=self.erc20_abi
            )
            
            decimals_a = token_a_contract.functions.decimals().call()
            decimals_b = token_b_contract.functions.decimals().call()
            
            # Convert amounts to wei
            amount_a_wei = int(amount_a * (10 ** decimals_a))
            amount_b_wei = int(amount_b * (10 ** decimals_b))
            
            # Calculate minimum amounts (with slippage)
            slippage = params.get('slippage', 0.5) / 100  # 0.5% default
            amount_a_min = int(amount_a_wei * (1 - slippage))
            amount_b_min = int(amount_b_wei * (1 - slippage))
            
            # Set deadline
            deadline = int(time.time()) + params.get('deadline', 1200)  # 20 minutes
            
            # Build transaction
            tx = router_contract.functions.addLiquidity(
                Web3.to_checksum_address(token_a),
                Web3.to_checksum_address(token_b),
                amount_a_wei,
                amount_b_wei,
                amount_a_min,
                amount_b_min,
                Web3.to_checksum_address(self.address),
                deadline
            ).build_transaction({
                'from': self.address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.address)
            })
            
            # Sign and send
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': receipt['status'] == 1,
                'tx_hash': tx_hash.hex(),
                'token_a': token_a,
                'token_b': token_b,
                'amount_a': amount_a,
                'amount_b': amount_b,
                'gas_used': receipt['gasUsed']
            }
        except Exception as e:
            raise Exception(f"Failed to add liquidity: {str(e)}")


# Usage Example
if __name__ == "__main__":
    # Initialize DEX
    dex = DEXExchange({
        'rpcUrl': 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
        'privateKey': 'YOUR_PRIVATE_KEY',  # Optional
        'poa': False  # Set to True for Polygon, BSC, etc.
    })
    
    try:
        # Fetch DeFi positions
        positions = dex.fetch_positions()
        print("DeFi Positions:")
        for pos in positions:
            print(f"  {pos['symbol']}: {pos['balance']}")
        
        # Check approvals for USDC
        if dex.address:
            usdc_address = dex.common_tokens['USDC']
            approvals = dex.fetch_approvals(usdc_address)
            print(f"\nUSDC Approvals:")
            for approval in approvals:
                print(f"  {approval['spender_name']}: {approval['allowance']}")
        
        # Example: Approve USDC for Uniswap (if private key provided)
        if dex.account:
            approval_result = dex.approve_token(
                dex.common_tokens['USDC'],
                dex.contracts['uniswap_v2_router']
            )
            print(f"\nApproval result: {approval_result}")
            
    except Exception as e:
        print(f"Error: {e}")