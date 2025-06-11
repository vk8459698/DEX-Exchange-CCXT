import { DexClient } from "./DexClient.js";
import { ethers } from "ethers";
import { provider } from "./setup.js";

const UNISWAP_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f";
const UNISWAP_FACTORY_ABI = [
  "function getPair(address tokenA, address tokenB) external view returns (address)"
];

const UNISWAP_PAIR_ABI = [
  "function getReserves() view returns (uint112, uint112, uint32)",
  "function token0() view returns (address)",
  "function token1() view returns (address)",
  "function totalSupply() view returns (uint256)",
  "function balanceOf(address owner) view returns (uint256)"
];

export class UniswapV2Client extends DexClient {
  async getPosition(tokenA: string, tokenB: string) {
    const factory = new ethers.Contract(UNISWAP_FACTORY, UNISWAP_FACTORY_ABI, provider);
    const pairAddress = await factory.getPair(tokenA, tokenB);

    if (pairAddress === ethers.ZeroAddress) return null;

    const pair = new ethers.Contract(pairAddress, UNISWAP_PAIR_ABI, provider);

    const [res0, res1] = await pair.getReserves();
    const [token0, token1] = await Promise.all([pair.token0(), pair.token1()]);
    const userLPBalance: bigint = await pair.balanceOf(this.wallet.address);
    const totalSupply: bigint = await pair.totalSupply();

    // Calculate user's share of the pool with 18 decimals
    const userShare = (userLPBalance * 10n ** 18n) / totalSupply;

    return {
      pairAddress,
      token0,
      token1,
      reserve0: res0.toString(),
      reserve1: res1.toString(),
      userLPBalance: userLPBalance.toString(),
      totalSupply: totalSupply.toString(),
      userShare: userShare.toString(), // raw big int scaled by 1e18
    };
  }
}
