/**
 * 0G Compute — list providers and generate inference credentials.
 * Usage:
 *   node compute_setup.mjs list              # list all providers
 *   node compute_setup.mjs deposit <amount>  # deposit OG tokens to ledger
 *   node compute_setup.mjs fund <provider>   # fund sub-account for provider
 *   node compute_setup.mjs key <provider>    # get Bearer token for provider
 */
import { createZGComputeNetworkBroker } from '@0glabs/0g-serving-broker';
import { ethers } from 'ethers';

const _log = console.log;
console.log = (...a) => process.stderr.write(a.join(' ') + '\n');
console.warn = (...a) => process.stderr.write(a.join(' ') + '\n');

const rpcUrl     = process.env.OG_RPC_URL     || 'https://evmrpc-testnet.0g.ai';
const privateKey = process.env.WALLET_PRIVATE_KEY;

if (!privateKey) {
  process.stderr.write('WALLET_PRIVATE_KEY not set\n');
  process.exit(1);
}

const provider = new ethers.JsonRpcProvider(rpcUrl);
const signer   = new ethers.Wallet(privateKey, provider);

const cmd = process.argv[2] || 'list';

try {
  const broker = await createZGComputeNetworkBroker(signer, 0);   // 0 = no pre-deposit

  if (cmd === 'list') {
    const services = await broker.inference.listService();
    _log(JSON.stringify(services, null, 2));

  } else if (cmd === 'deposit') {
    const amount = parseFloat(process.argv[3] || '1');
    await broker.ledger.depositFund(amount);
    process.stderr.write(`Deposited ${amount} OG to ledger\n`);
    _log(JSON.stringify({ deposited: amount }));

  } else if (cmd === 'fund') {
    const providerAddr = process.argv[3];
    if (!providerAddr) { process.stderr.write('Usage: fund <provider_address>\n'); process.exit(1); }
    await broker.inference.addOrUpdateService(providerAddr, 0.5);
    process.stderr.write(`Funded ${providerAddr} with 0.5 OG\n`);
    _log(JSON.stringify({ funded: providerAddr }));

  } else if (cmd === 'key') {
    const providerAddr = process.argv[3];
    if (!providerAddr) { process.stderr.write('Usage: key <provider_address>\n'); process.exit(1); }
    const meta = await broker.inference.getServiceMetadata(providerAddr);
    process.stderr.write(`Provider endpoint: ${meta.endpoint}\n`);
    process.stderr.write(`Provider model: ${meta.model}\n`);
    // Generate a one-time request header (can be adapted for permanent key)
    const headers = await broker.inference.getRequestHeaders(providerAddr, 'test');
    _log(JSON.stringify({ endpoint: meta.endpoint, model: meta.model, headers }));

  } else {
    process.stderr.write(`Unknown command: ${cmd}\n`);
    process.exit(1);
  }
} catch (err) {
  process.stderr.write(`Error: ${err.message}\n`);
  process.exit(1);
}
