# DEX Exchange CCXT Implementation

A custom CCXT-compatible exchange class for interacting with Decentralized Exchanges (DEX) on Ethereum and EVM-compatible chains. This implementation focuses on DeFi position management and token approval handling.

## Features

### Core Functionality
- **DeFi Position Management**: Track token balances across multiple wallets
- **Token Approval Management**: Handle ERC-20 token approvals for DEX interactions
- **Multi-DEX Support**: Compatible with Uniswap V2/V3, SushiSwap, PancakeSwap
- **Cross-Chain Support**: Works with Ethereum mainnet, Polygon, BSC, and other EVM chains

### Key Capabilities
- Fetch wallet token positions with real-time balances
- Monitor and manage token approvals for DEX routers
- Approve/revoke token spending permissions
- Add liquidity to DEX pools
- CCXT-compatible interface for seamless integration

## Installation

```bash
pip install ccxt web3 python-dotenv
```

## Configuration

### Environment Setup
Create a `.env` file:

```env
RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_private_key_here  # Optional, for write operations
WALLET_ADDRESS=0x742d35Cc6634C0532925a3b8D4e3dD89c41296692  # Optional, for read-only
```

### Supported Networks
- **Ethereum Mainnet**: Default configuration
- **Polygon**: Set `poa: True` in config
- **Binance Smart Chain**: Set `poa: True`, use BSC RPC URL
- **Other EVM chains**: Compatible with any EVM-compatible network

## Usage

### Basic Setup

```python
from dex_exchange import DEXExchange

# Initialize with config
dex = DEXExchange({
    'rpcUrl': 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
    'privateKey': 'YOUR_PRIVATE_KEY',  # Optional for read operations
    'poa': False  # Set True for Polygon, BSC
})
```

### Fetching DeFi Positions

```python
# Get all token positions for connected wallet
positions = dex.fetch_positions()

for position in positions:
    print(f"{position['symbol']}: {position['balance']}")
    print(f"  Contract: {position['address']}")
    print(f"  Decimals: {position['decimals']}")
```

### Managing Token Approvals

```python
# Check USDC approvals for all DEX routers
usdc_address = dex.common_tokens['USDC']
approvals = dex.fetch_approvals(usdc_address)

for approval in approvals:
    print(f"{approval['spender_name']}: {approval['allowance']}")
    if approval['is_unlimited']:
        print(" Unlimited approval detected!")
```

### Approving Tokens

```python
# Approve USDC for Uniswap V2 Router
approval_result = dex.approve_token(
    token_address=dex.common_tokens['USDC'],
    spender_address=dex.contracts['uniswap_v2_router'],
    amount=1000  # Approve 1000 USDC, or None for unlimited
)

print(f"Transaction Hash: {approval_result['tx_hash']}")
print(f"Success: {approval_result['success']}")
```

### Revoking Approvals

```python
# Revoke USDC approval for a specific router
revoke_result = dex.revoke_approval(
    token_address=dex.common_tokens['USDC'],
    spender_address=dex.contracts['uniswap_v2_router']
)
```

### Adding Liquidity

```python
# Add liquidity to USDC/WETH pool
liquidity_result = dex.add_liquidity(
    token_a=dex.common_tokens['USDC'],
    token_b=dex.common_tokens['WETH'],
    amount_a=1000,  # 1000 USDC
    amount_b=0.5,   # 0.5 WETH
    params={
        'slippage': 0.5,  # 0.5% slippage tolerance
        'deadline': 1200  # 20 minutes deadline
    }
)
```

## Supported Tokens

The class includes common token addresses for Ethereum mainnet:

- **USDC**: USD Coin (`0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`)
- **USDT**: Tether (`0xdAC17F958D2ee523a2206206994597C13D831ec7`)
- **WBTC**: Wrapped Bitcoin (`0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599`)
- **WETH**: Wrapped Ether (`0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2`)
- **DAI**: Dai Stablecoin (`0x6B175474E89094C44Da98b954EedeAC495271d0F`)

## Supported DEX Routers

- **Uniswap V2**: `0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D`
- **Uniswap V3**: `0xE592427A0AEce92De3Edee1F18E0157C05861564`
- **SushiSwap**: `0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F`
- **PancakeSwap**: `0x10ED43C718714eb63d5aA57B78B54704E256024E` (BSC)

## Error Handling

The class includes comprehensive error handling:

```python
try:
    positions = dex.fetch_positions()
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Network or contract error: {e}")
```

## Security Considerations

### Private Key Safety
- **Never commit private keys to version control**
- Use environment variables or secure key management
- Consider using read-only mode for position monitoring

### Approval Management
- Monitor unlimited approvals regularly
- Revoke unused approvals to minimize risk
- Use specific amounts instead of unlimited approvals when possible

### Gas Optimization
- Check gas prices before transactions
- Use appropriate gas limits for different operations
- Consider batching multiple operations

## CCXT Integration

This class extends CCXT's base Exchange class, providing compatibility with CCXT workflows:

```python
# CCXT-style balance fetching
balance = dex.fetch_balance()
print(balance['USDC']['free'])  # Available USDC balance

# CCXT-style market loading
markets = dex.load_markets()
```

## Limitations & Future Enhancements

### Current Limitations
- **Read-heavy operations**: Optimized for monitoring rather than high-frequency trading
- **Limited DEX protocols**: Currently supports Uniswap-style AMM DEXs
- **No orderbook DEXs**: Focused on AMM (Automated Market Maker) protocols

### Planned Enhancements
- **Liquidity position tracking**: Monitor LP tokens and yield farming positions
- **Staking position management**: Track staking rewards and positions
- **Multi-chain portfolio view**: Aggregate positions across multiple chains
- **Price integration**: Real-time token pricing from DEX pools
- **Advanced order types**: Limit orders, stop-losses via DEX aggregators

