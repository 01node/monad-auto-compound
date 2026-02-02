#!/usr/bin/env python3
"""
Automated compounding script for Monad.
- Claims pending rewards from validator
- Gets wallet balance
- Stakes (balance - reserve) to validator

Usage: python auto_compound.py [--config config.toml] [--dry-run]
"""

import os
import sys
import toml
import argparse
from web3 import Web3

from staking_sdk_py.generateCalldata import claim_rewards, delegate
from staking_sdk_py.callGetters import call_getter
from staking_sdk_py.generateTransaction import send_transaction
from staking_sdk_py.signer_factory import LocalSigner

WEI_PER_MON = 1_000_000_000_000_000_000


def load_config(config_path: str) -> dict:
    if not os.path.isfile(config_path):
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path, "r") as f:
        return toml.load(f)


def wei_to_mon(wei_amount: int) -> float:
    return wei_amount / WEI_PER_MON


def mon_to_wei(mon_amount: int) -> int:
    return mon_amount * WEI_PER_MON


def main():
    parser = argparse.ArgumentParser(description="Auto restake MON rewards")
    parser.add_argument("--config", type=str, default="./config.toml", help="Path to config file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without executing")
    args = parser.parse_args()

    config = load_config(args.config)

    # Read config
    rpc_url = config["network"]["rpc_url"]
    chain_id = config["network"]["chain_id"]
    contract_address = config["network"]["contract_address"]

    private_key = config["staking"]["private_key"]
    validator_id = config["staking"]["validator_id"]
    reserve_mon = config["staking"]["reserve_mon"]

    if private_key == "0xYOUR_PRIVATE_KEY_HERE":
        print("ERROR: Set your private_key in config.toml")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        print(f"ERROR: Cannot connect to RPC: {rpc_url}")
        sys.exit(1)

    signer = LocalSigner(private_key)
    delegator_address = signer.get_address()

    print(f"=== Monad Auto-Compound ===")
    print(f"Validator ID: {validator_id}")
    print(f"Wallet: {delegator_address}")
    print(f"Reserve: {reserve_mon} MON")
    print()

    # Step 1: Check delegator info and pending rewards
    try:
        delegator_info = call_getter(w3, 'get_delegator', contract_address, validator_id, delegator_address)
        if not delegator_info:
            print(f"ERROR: Could not fetch delegator info")
            sys.exit(1)

        active_stake = delegator_info[0]
        pending_stake = delegator_info[1]
        rewards = delegator_info[2]

        print(f"Current stake: {wei_to_mon(active_stake):.4f} MON (active) + {wei_to_mon(pending_stake):.4f} MON (pending)")
        print(f"Pending rewards: {wei_to_mon(rewards):.4f} MON")
    except Exception as e:
        print(f"ERROR: Failed to get delegator info: {e}")
        sys.exit(1)

    # Step 2: Claim rewards if any
    if rewards > 0:
        print(f"\n>>> Claiming {wei_to_mon(rewards):.4f} MON rewards...")

        if args.dry_run:
            print("  [DRY RUN] Would claim rewards")
        else:
            try:
                calldata = claim_rewards(validator_id)
                tx_hash = send_transaction(w3, signer, contract_address, calldata, chain_id, 0)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status == 1:
                    print(f"  SUCCESS: Claimed rewards (tx: 0x{receipt.transactionHash.hex()})")
                else:
                    print(f"  FAILED: Claim transaction failed")
                    sys.exit(1)
            except Exception as e:
                print(f"  ERROR: Failed to claim rewards: {e}")
                sys.exit(1)
    else:
        print("\nNo pending rewards to claim")

    # Step 3: Get wallet balance
    balance = w3.eth.get_balance(delegator_address)
    balance_mon = wei_to_mon(balance)
    print(f"\nWallet balance: {balance_mon:.4f} MON")

    # Step 4: Calculate stake amount (balance - reserve)
    reserve_wei = mon_to_wei(reserve_mon)
    stake_amount_wei = balance - reserve_wei

    if stake_amount_wei <= 0:
        print(f"\nInsufficient balance to stake. Need more than {reserve_mon} MON")
        print("Nothing to restake. Done.")
        sys.exit(0)

    stake_amount_mon = int(wei_to_mon(stake_amount_wei))  # Round down to whole MON
    stake_amount_wei = mon_to_wei(stake_amount_mon)

    if stake_amount_mon <= 0:
        print("\nStake amount rounds to 0 MON. Nothing to restake.")
        sys.exit(0)

    print(f"\n>>> Staking {stake_amount_mon} MON to validator {validator_id}...")

    if args.dry_run:
        print("  [DRY RUN] Would delegate stake")
    else:
        try:
            calldata = delegate(validator_id)
            tx_hash = send_transaction(w3, signer, contract_address, calldata, chain_id, stake_amount_wei)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                print(f"  SUCCESS: Staked {stake_amount_mon} MON (tx: 0x{receipt.transactionHash.hex()})")
            else:
                print(f"  FAILED: Delegate transaction failed")
                sys.exit(1)
        except Exception as e:
            print(f"  ERROR: Failed to delegate: {e}")
            sys.exit(1)

    # Final summary
    print(f"\n=== Complete ===")
    final_balance = w3.eth.get_balance(delegator_address)
    print(f"Remaining balance: {wei_to_mon(final_balance):.4f} MON")


if __name__ == "__main__":
    main()
