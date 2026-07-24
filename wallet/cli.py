"""Interactive Helix wallet CLI."""

import getpass
import json

from node.transaction import Transaction
from wallet.network import (
    get_balance, get_chain, get_health, get_history, get_node_stats, get_pending,
    get_transaction, mine, send_transaction,
)
from wallet.wallet_manager import (
    add_watch_only_wallet, change_wallet_password, create_wallet, delete_wallet,
    export_wallet_backup, get_wallet_info, list_wallets, recover_wallet,
    unlock_wallet,
)

current_wallet = None
current_wallet_name = None


def help():
    print("""
Commands:
  create-wallet NAME              Create an encrypted wallet
  recover-wallet NAME             Recover from a seed phrase
  import-watch NAME ADDRESS       Add a watch-only address
  wallets                         List wallet names, addresses, and types
  wallet-info [NAME]              Show non-secret wallet metadata
  use NAME                        Unlock and select a wallet
  lock                            Forget the unlocked wallet from memory
  change-password NAME            Re-encrypt a wallet with a new password
  delete-wallet NAME              Delete a wallet after confirmation
  backup PATH                     Export the encrypted wallet store
  address                         Show selected wallet address
  balance                         Show confirmed balance
  history [OFFSET] [LIMIT]        Show paginated transaction history
  mine                            Mine pending transactions
  send ADDRESS AMOUNT             Sign and submit a transaction
  pending                         Show pending transactions
  tx ID                           View a transaction
  chain                           Show blockchain
  status                          Show connected node status
  health                          Check whether a node is reachable
  help                            Show commands
  exit                            Quit
""")


def _password_pair(prompt="Set a password for this wallet: "):
    password = getpass.getpass(prompt)
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm or not password:
        print("Passwords did not match or were empty")
        return None
    return password


def _require_wallet():
    if current_wallet is None:
        print("Select an encrypted wallet first")
        return False
    return True


def _print_json(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main():
    global current_wallet, current_wallet_name
    while True:
        try:
            command = input("> ").split()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not command:
            continue
        action = command[0].lower()

        if action == "exit":
            break
        if action == "help":
            help()
        elif action == "create-wallet":
            if len(command) != 2:
                print("Usage: create-wallet NAME")
                continue
            password = _password_pair()
            if password:
                wallet = create_wallet(command[1], password)
                print("Created:", wallet.address if wallet else "wallet already exists")
        elif action == "recover-wallet":
            if len(command) != 2:
                print("Usage: recover-wallet NAME")
                continue
            phrase = input("Enter your recovery phrase: ").strip()
            password = _password_pair()
            if phrase and password:
                wallet = recover_wallet(command[1], phrase, password)
                print("Recovered:", wallet.address if wallet else "wallet already exists")
        elif action == "import-watch":
            if len(command) != 3:
                print("Usage: import-watch NAME ADDRESS")
                continue
            print("Watch-only wallet added" if add_watch_only_wallet(command[1], command[2]) else "Could not add wallet")
        elif action == "wallets":
            _print_json(list_wallets(detailed=True))
        elif action == "wallet-info":
            name = command[1] if len(command) > 1 else current_wallet_name
            _print_json(get_wallet_info(name) if name else {"message": "Specify a wallet"})
        elif action == "use":
            if len(command) != 2:
                print("Usage: use NAME")
                continue
            wallet = unlock_wallet(command[1], getpass.getpass("Password: "))
            if wallet:
                current_wallet, current_wallet_name = wallet, command[1]
                print("Wallet selected:", wallet.address)
            else:
                print("Wrong name/password or wallet is watch-only")
        elif action == "lock":
            current_wallet = current_wallet_name = None
            print("Wallet locked")
        elif action == "change-password":
            if len(command) != 2:
                print("Usage: change-password NAME")
                continue
            old = getpass.getpass("Current password: ")
            new = _password_pair("New password: ")
            if new:
                print("Password changed" if change_wallet_password(command[1], old, new) else "Wrong wallet or password")
        elif action == "delete-wallet":
            if len(command) != 2:
                print("Usage: delete-wallet NAME")
                continue
            if input(f"Type DELETE {command[1]} to confirm: ") != f"DELETE {command[1]}":
                print("Cancelled")
                continue
            info = get_wallet_info(command[1]) or {}
            password = None if info.get("type") == "watch-only" else getpass.getpass("Password: ")
            if delete_wallet(command[1], password):
                if current_wallet_name == command[1]:
                    current_wallet = current_wallet_name = None
                print("Wallet deleted")
            else:
                print("Could not delete wallet")
        elif action == "backup":
            if len(command) != 2:
                print("Usage: backup PATH")
                continue
            print("Backup written to", export_wallet_backup(command[1]))
        elif action == "address":
            print(current_wallet.address if current_wallet else "No wallet selected")
        elif action == "balance":
            if _require_wallet():
                _print_json(get_balance(current_wallet.address))
        elif action == "history":
            if _require_wallet():
                try:
                    offset = int(command[1]) if len(command) > 1 else 0
                    limit = int(command[2]) if len(command) > 2 else 50
                except ValueError:
                    print("Usage: history [OFFSET] [LIMIT]")
                    continue
                _print_json(get_history(current_wallet.address, offset=offset, limit=limit))
        elif action == "status":
            _print_json(get_node_stats())
        elif action == "health":
            _print_json(get_health())
        elif action == "mine":
            if _require_wallet():
                _print_json(mine(current_wallet.address))
        elif action == "pending":
            _print_json(get_pending())
        elif action == "chain":
            _print_json(get_chain())
        elif action == "send":
            if not _require_wallet():
                continue
            if len(command) != 3:
                print("Usage: send ADDRESS AMOUNT")
                continue
            try:
                amount = int(command[2])
            except ValueError:
                print("Amount must be an integer")
                continue
            tx = Transaction(current_wallet.address, command[1], amount)
            tx.public_key = current_wallet.public_key
            tx.sign(current_wallet.private_key)
            result = send_transaction({
                "sender": tx.sender, "receiver": tx.receiver, "amount": tx.amount,
                "signature": tx.signature, "public_key": current_wallet.public_key_string(),
                "tx_id": tx.tx_id,
            })
            _print_json(result)
            print("Transaction ID:", tx.tx_id)
        elif action == "tx":
            if len(command) != 2:
                print("Usage: tx TRANSACTION_ID")
                continue
            _print_json(get_transaction(command[1]))
        else:
            print("Unknown command")


if __name__ == "__main__":
    main()
