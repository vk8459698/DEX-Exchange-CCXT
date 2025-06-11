import { UniswapV2Client } from "./UniswapV2Client.js";
import { wallet, provider } from "./setup.js"; // make sure provider is exported from setup.js
import { ethers } from "ethers";

const main = async () => {
  const client = new UniswapV2Client(wallet);

  const balance = await provider.getBalance(wallet.address);
  console.log("Wallet address:", wallet.address);
  console.log("Wallet balance:", ethers.formatEther(balance), "ETH");

  const WETH = ethers.getAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2");
  const DAI  = ethers.getAddress("0x6B175474E89094C44Da98b954EedeAC495271d0F");

  console.log("Checking Uniswap V2 LP Position for WETH-DAI...");
  const pos = await client.getPosition(WETH, DAI);
  console.log(pos);

  const spender = "0x1111111254EEB25477B68fb85Ed929f73A960582"; // Example
  const approved = await client.checkApproval(DAI, spender);
  console.log("DAI Approved?", approved);

  if (!approved) {
    console.log("Approving...");
    await client.approveToken(DAI, spender, ethers.MaxUint256);
    console.log("Approved!");
  }
};

main().catch(console.error);
