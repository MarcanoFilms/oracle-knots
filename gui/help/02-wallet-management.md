# Wallet Management Guide

Learn how to create, load, and manage wallets in Oracle Knots.

## Creating a Wallet

1. Go to **Wallet Manager**
2. Enter a wallet name (e.g., "sovereign_wallet")
3. Click "Create New Wallet"
4. Your wallet is now loaded and ready to use

## Loading an Existing Wallet

1. Go to **Wallet Manager**
2. Click "Load Wallet"
3. Select a wallet from your file system
4. The wallet will be loaded and available for transactions

## Receiving Bitcoin

1. Go to **Wallet Manager** → **Receive** tab
2. Select an address type (Taproot recommended for newest addresses)
3. Click "Generate Receive Address"
4. Share the address or QR code with the sender
5. The Bitcoin will appear in your wallet when received

## Sending Bitcoin

### Simple Send
1. Go to **Wallet Manager** → **Send** tab
2. Enter the recipient address
3. Enter the amount in BTC
4. Set the fee rate (leave blank for automatic)
5. Click "Send Transaction"

### Coin Control Send
1. Go to **Wallet Manager** → **Send** tab
2. Click the "Coin Control" tab
3. Select specific UTXOs (unspent outputs) to spend
4. Enter recipient and amount
5. Click "Send with Selected Coins"

Coin Control allows you to choose exactly which outputs to spend, giving you maximum privacy and control.

## Managing UTXOs

1. Go to **Wallet Manager** → **UTXOs** tab
2. View all your unspent Bitcoin outputs
3. Lock important UTXOs to prevent accidental spending
4. Click on a UTXO to see details

## Wallet Security

1. Go to **Wallet Manager** → **Tools** → **Security**
2. **Encrypt Wallet**: Set a passphrase to protect your private keys
3. **Backup Wallet**: Create a backup file (.dat) to restore later
4. **Unlock/Lock**: Temporarily unlock your wallet for spending

### Important: Always Backup!
Before sending Bitcoin, create a backup of your wallet. Without a backup, you risk losing your Bitcoin permanently.

## PSBT (Partially Signed Bitcoin Transaction)

Use PSBTs for advanced workflows:
1. Go to **Wallet Manager** → **Tools** → **PSBT**
2. **Decode**: View a PSBT's contents
3. **Sign**: Add your signatures to a PSBT
4. **Finalize & Broadcast**: Complete and send the transaction

PSBTs are useful for multisig wallets and hardware wallet integration.

## Viewing Transaction History

1. Go to **Wallet Manager** → **History** tab
2. View your recent transactions
3. Use the search and filters to find specific transactions
4. Click on a transaction to see details

## Managing Addresses

1. Go to **Wallet Manager** → **Addresses** tab
2. View all addresses in your wallet
3. Hover over an address to see its full value
4. Label important addresses for your records
