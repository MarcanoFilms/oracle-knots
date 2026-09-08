# The BLAKE2b chain (XBT)

Oracle Knots follows the **BLAKE2b proof-of-work fork of Bitcoin** — a chain that
replaces SHA-256d mining with **BLAKE2b** and adds a new block header format.
The community ticker is **XBT** (listed as **BTCB2** on the Neoxa exchange).

## What changed vs. classic Bitcoin

| Aspect | Classic Bitcoin | BLAKE2b chain |
|---|---|---|
| PoW hash | SHA-256d | **BLAKE2b** |
| Block header | v1, 80 bytes | **v2, extended** (height, tx-count commitment, ASIC profile, time offset) |
| Activation | — | **mainnet height 961640** (testnet4 150308) |
| Sighash | legacy/segwit/taproot | same + **opt-in unified sighash** (bit `0x20`) |

- **Activation is a buried deployment** (`DEPLOYMENT_BLAKE2B`). Blocks at/after
  the activation height must use BLAKE2b PoW and header v2.
- **Consensus-critical headline:** the first BLAKE2b block's coinbase must carry
  the canonical `blake2b_headline` (set in `bitcoin.conf`). If it is wrong or
  empty, the node rejects the first BLAKE2b block. Keep it exact.
- **Header v2** commits to the block's transaction count (fixes CVE-2017-12842),
  includes the block height, and reserves a merge-mining hook for future use.

## Why standard wallets can't connect

Light and desktop wallets (Electrum, online Sparrow, BlueWallet) validate the
header chain **client-side**, expecting 80-byte SHA-256d headers. This chain's
v2 headers are rejected outright — no amount of electrs/Fulcrum in between helps,
because the failing check is in the client, not the server.

**The consequence:** to see and spend XBT you need software that understands the
fork — i.e. this node plus **Oracle Wallet** (see [WALLET.md](WALLET.md)).

## Unified sighash (opt-in)

The fork adds `SighashRules::UNIFIED`. Signing opts in via the `SIGHASH_UNIFIED`
(`0x20`) bit; verification accepts a legacy signature too. In practice standard
`SIGHASH_ALL` signatures remain valid on this chain, so spending coinbase rewards
via a normal PSBT flow works without unified sighash.

> **Replay caution:** a legacy signature over a UTXO that predates the fork
> (< height 961640) could be replayed on the SHA-256d chain. Never mix pre-fork
> and post-fork inputs in one transaction.

## Operating a node on this chain

Recommended `bitcoin.conf` essentials:

```ini
consensusrules=rdts                 # BIP-110 / RDTS signaling
blake2b_headline=<exact canonical headline>
```

See [MINING.md](MINING.md) for turning the node into a sovereign miner, and
[BUILD.md](BUILD.md) to compile.
