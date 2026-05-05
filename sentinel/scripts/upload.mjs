/**
 * 0G Storage upload script (ESM) — called from Python via subprocess.
 * Usage: node upload.mjs <filepath>
 * Prints JSON: { "rootHash": "...", "txHash": "..." }
 *
 * Requires: npm install @0gfoundation/0g-ts-sdk ethers
 */
import { ZgFile, Indexer } from '@0gfoundation/0g-ts-sdk';
import { ethers } from 'ethers';
import { readFileSync } from 'fs';

// Redirect all console.log/warn to stderr so only the final JSON reaches stdout.
// The 0G SDK emits verbose debug logs via console.log which would break JSON parsing.
const _stderr = (...a) => process.stderr.write(a.join(' ') + '\n');
console.log  = _stderr;
console.warn = _stderr;

const filePath   = process.argv[2];
const rpcUrl     = process.env.OG_RPC_URL;
const indexerUrl = process.env.OG_INDEXER_URL;
const privateKey = process.env.WALLET_PRIVATE_KEY;

if (!filePath) {
  console.error('Usage: node upload.mjs <filepath>');
  process.exit(1);
}

try {
  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const signer   = new ethers.Wallet(privateKey, provider);
  const indexer  = new Indexer(indexerUrl);

  const file = await ZgFile.fromFilePath(filePath);
  const [tree, treeErr] = await file.merkleTree();
  if (treeErr) throw new Error(`Merkle tree: ${treeErr}`);

  const rootHash = tree.rootHash();

  const [txResult, uploadErr] = await indexer.upload(file, rpcUrl, signer, {});
  if (uploadErr) throw new Error(`Upload: ${uploadErr}`);
  const txHash = (typeof txResult === 'string') ? txResult : (txResult?.txHash ?? String(txResult));

  await file.close();
  process.stdout.write(JSON.stringify({ rootHash, txHash }) + '\n');
} catch (err) {
  process.stderr.write(err.message + '\n');
  process.exit(1);
}
