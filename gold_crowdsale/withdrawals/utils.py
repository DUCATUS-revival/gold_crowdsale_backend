import sys
import logging

from bip32utils import BIP32Key
from eth_keys import keys
from web3.exceptions import TransactionNotFound

from gold_crowdsale.crypto_api.eth import load_w3


def get_private_keys(root_private_key, child_id):
    root = BIP32Key.fromExtendedKey(root_private_key)
    eth_private = keys.PrivateKey(root.ChildKey(child_id).k.to_string())
    btc_private = root.ChildKey(child_id).WalletImportFormat()
    return eth_private, btc_private


def normalize_gas_price(gas_price):
    gwei_decimals = 10 ** 9
    gas = int(round(gas_price / gwei_decimals, 0)) * gwei_decimals
    lower_gas = gas - 1 if gas > 2 else gas
    return gas, lower_gas


def check_tx_success(tx):
    web3 = load_w3('ETH')
    try:
        receipt = web3.eth.getTransactionReceipt(tx)
        if receipt['status'] == 1:
            return True
        else:
            return False
    except TransactionNotFound:
        return False


def check_tx(tx):
        tx_found = False

        logging.info(f'Checking transaction {tx} until found in network')
        tx_found = check_tx_success(tx)
        if tx_found:
            logging.info(f'Ok, found transaction {tx} and it was completed')
            return True


if __name__ == '__main__':
    root_pk = sys.argv[1]
    child_id_value = int(sys.argv[2])
    eth_priv = get_private_keys(root_pk, child_id_value)
    print(f'private keys for child with id {child_id_value}:\neth: {eth_priv}', flush=True)
