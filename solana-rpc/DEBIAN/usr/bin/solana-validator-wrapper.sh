#!/bin/bash

# Load environment variables
source /etc/solana-rpc/config.env

# Construct the command
cmd="solana-validator \
    --identity $SOLANA_VALIDATOR_IDENTITY \
    --known-validator $SOLANA_KNOWN_VALIDATORS \
    $SOLANA_ONLY_KNOWN_RPC \
    $SOLANA_FULL_RPC_API \
    $SOLANA_NO_VOTING \
    --ledger $SOLANA_LEDGER_DIR \
    --accounts $SOLANA_ACCOUNTS_DIR \
    --log $SOLANA_LOG_FILE \
    --rpc-port $SOLANA_RPC_PORT \
    --rpc-bind-address $SOLANA_RPC_BIND_ADDRESS \
    $SOLANA_PRIVATE_RPC \
    --dynamic-port-range $SOLANA_DYNAMIC_PORT_RANGE \
    --entrypoint $SOLANA_ENTRYPOINTS \
    --expected-genesis-hash $SOLANA_EXPECTED_GENESIS_HASH \
    $SOLANA_WAL_RECOVERY_MODE \
    $SOLANA_LIMIT_LEDGER_SIZE"

# Execute the command
exec $cmd
