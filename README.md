# Monad Auto-Compound

Automated script for Monad staking that claims pending rewards and compounds your wallet balance to a validator.

## What it does

1. Claims pending staking rewards from your validator
2. Gets your wallet balance
3. Stakes `(balance - reserve)` back to the validator
4. Keeps a configurable amount (default 100 MON) for gas fees

## Requirements

- Python 3.8+
- A funded Monad wallet
- Existing delegation to a validator

## Dependencies

This project uses [staking_sdk_py](https://github.com/monad-developers/staking-sdk-cli) from Monad Developers for interacting with the staking contract.

## Installation

```bash
git clone https://github.com/01node/monad-auto-compound.git
cd monad-auto-compound

python3 -m venv venv
source venv/bin/activate
pip install .
```

## Configuration

Edit `config.toml`:

```toml
[network]
rpc_url = "https://rpc-testnet.monadinfra.com"
chain_id = 10143  # testnet (use 143 for mainnet)
contract_address = "0x0000000000000000000000000000000000001000"

[staking]
private_key = "0xYOUR_PRIVATE_KEY_HERE"
validator_id = 14
reserve_mon = 100
```

| Field | Description |
|-------|-------------|
| `rpc_url` | Monad RPC endpoint |
| `chain_id` | 10143 for testnet, 143 for mainnet |
| `private_key` | Your wallet private key (with 0x prefix) |
| `validator_id` | The validator ID to stake to |
| `reserve_mon` | MON to keep in wallet for gas fees |

## Usage

### Dry Run (test without executing)

```bash
python auto_compound.py --dry-run
```

### Execute

```bash
python auto_compound.py
```

### Example Output

```
=== Monad Auto-Compound ===
Validator ID: 14
Wallet: 0xF2Fff6CEd59c1d45257a7e6B316a8cEeF7958293
Reserve: 100 MON

Current stake: 100000.0000 MON (active)
Pending rewards: 13752.7499 MON

>>> Claiming 13752.7499 MON rewards...
  SUCCESS: Claimed rewards (tx: 0xf1318b3a...)

Wallet balance: 13935.9676 MON

>>> Staking 13835 MON to validator 14...
  SUCCESS: Staked 13835 MON (tx: 0xadf0e243...)

=== Complete ===
Remaining balance: 100.8666 MON
```

## Cron Setup (Automated)

Run automatically every 6 hours:

```bash
crontab -e
```

Add:

```
0 */6 * * * cd /home/monad/monad-auto-compound && /home/monad/monad-auto-compound/venv/bin/python auto_compound.py >> /home/monad/monad-auto-compound/compound.log 2>&1
```

## Security

- Never commit `config.toml` with your private key
- Add `config.toml` to `.gitignore`
- Consider using environment variables for the private key in production

## License

MIT
