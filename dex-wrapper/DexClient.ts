import { ethers } from "ethers";
import { provider, wallet } from "./setup.js";

export class DexClient {
  wallet: ethers.Wallet;

  constructor(wallet: ethers.Wallet) {
    this.wallet = wallet;
  }

  async checkApproval(tokenAddress: string, spender: string): Promise<boolean> {
    const abi = [
      "function allowance(address owner, address spender) view returns (uint256)"
    ];
    const token = new ethers.Contract(tokenAddress, abi, provider);
    const allowance: bigint = await token.allowance(this.wallet.address, spender);
    return allowance > 0n;
  }

  async approveToken(tokenAddress: string, spender: string, amount: ethers.BigNumberish) {
    const abi = [
      "function approve(address spender, uint256 amount) returns (bool)"
    ];
    const token = new ethers.Contract(tokenAddress, abi, this.wallet);
    const tx = await token.approve(spender, amount);
    return tx.wait();
  }
}
