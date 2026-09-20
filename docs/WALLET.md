# Oracle Wallet — spend & sign XBT

Standard wallets can't connect to the BLAKE2b chain (they reject its v2 headers —
see [BLAKE2B.md](BLAKE2B.md)). **Oracle Wallet** is a Shrike/Sparrow build with
BLAKE2b support that talks to **your** node's RPC to see balances, build, sign,
and broadcast XBT transactions — with hardware-wallet support.

The Control Center's **Wallet** tab shows an *Oracle Wallet* card with the
connection status and one-click **Configure connection** / **Open** buttons.

## Install

Oracle Wallet is the `privkeyio/shrike` build with BLAKE2b support (a Sparrow
fork). Install it into userspace (it does not touch the node), then confirm the
`oracle-wallet`/`shrike` launcher is on your `PATH`. Verify the download's GPG
signature and checksum before running.

## Connect it to your node (plug-and-play)

The node uses `rpcuser`/`rpcpassword` auth (cookie auth is disabled while those
are set, which is what DATUM needs). In the Control Center:

1. Open the **Wallet** tab → the **Oracle Wallet** card.
2. Click **Configure connection**. This writes Oracle Wallet's server settings
   from your node's `bitcoin.conf`:
   - Server type: **Bitcoin Core / Knots**
   - URL: `http://127.0.0.1:8332`
   - Auth: **User / Pass** (`rpcuser` + `rpcpassword`, *not* cookie)
   - It merges into the existing config and keeps a `.oracle-bak` backup.
3. Click **Open Oracle Wallet**.

> Oracle Wallet overwrites its own config on exit — configure it while it is
> **closed**.

## Seeing your balance / first spend

- If the balance shows **0** right after import, it's the scan window, not the
  derivation: use *"Scan for transactions earlier than…"* with a date before your
  first coinbase.
- Native SegWit derivation is the standard `m/84'/0'/0'`. The node may store the
  watch-only descriptor with a truncated origin (account-xpub fingerprint) that
  looks like `m/0/0`; the real path is still `m/84'/0'/0'/0/0`.
- Spending is a normal PSBT flow; a legacy `SIGHASH_ALL` signature is valid on
  this chain. For hardware signing, a Keystone must hold the same seed
  (matching master fingerprint) — note Keystone does **not** sign the opt-in
  unified sighash format.

## Security

- The Control Center never sends your `rpcpassword` to the browser (important in
  `--lan` mode); it only writes it locally into Oracle Wallet's config.
- Never commit a filled-in wallet or node config. Seeds stay on your device / in
  Oracle Wallet only.
