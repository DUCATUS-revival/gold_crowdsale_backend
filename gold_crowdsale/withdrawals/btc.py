import logging
import sys
import traceback

from gold_crowdsale.crypto_api.btc import BitcoinAPI, BitcoinRPC
from gold_crowdsale.purchases.models import TokenPurchase
from gold_crowdsale.settings import ROOT_KEYS, NETWORKS, DECIMALS
from gold_crowdsale.withdrawals.utils import get_private_keys


def withdraw_btc_funds():
    withdraw_parameters = {
        'root_private_key': ROOT_KEYS.get('private'),
        'root_public_key': ROOT_KEYS.get('public'),
        'address_to_btc': NETWORKS.get('BTC').get('withdraw_address')
    }

    for key, value in withdraw_parameters.items():
        if not value:
            logging.info(f'Value not found for parameter {key}. Aborting')
            return

    all_purchases = TokenPurchase.objects.all().exclude(btc_address=None)
    logging.info('BTC WITHDRAW')

    for user in all_purchases:
        eth_priv_key, btc_priv_key = get_private_keys(withdraw_parameters['root_private_key'], user.id)
        logging.info(f'BTC address: {user.btc_address}')
        try:
            process_withdraw_btc(withdraw_parameters, user, btc_priv_key)
        except Exception as e:
            logging.error('BTC withdraw failed. Error is:')
            logging.error(e)
            logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))


def process_withdraw_btc(params, account, priv_key):
    if isinstance(account, str):
        from_address = account
    else:
        from_address = account.btc_address

    to_address = params['address_to_btc']

    api = BitcoinAPI()
    inputs, value, response_ok = api.get_address_unspent_all(from_address)

    if not response_ok:
        logging.error(f'Failed to fetch information about BTC address {from_address}')
        return

    balance = int(value)
    if balance <= 0:
        balance = 0

    rpc = BitcoinRPC()
    transaction_fee = rpc.relay_fee
    if balance < transaction_fee:
        logging.info(f'Address skipped: {from_address}: balance {balance} < tx fee of {transaction_fee}')
        return

    withdraw_amount = (balance - transaction_fee) / DECIMALS['BTC']

    output_params = {to_address: withdraw_amount}

    logging.info(f'Withdraw tx params: from {from_address} to {to_address} on amount {withdraw_amount}')
    logging.info(f'input_params: {inputs}')
    logging.info(f'output_params: {output_params}')

    sent_tx_hash = rpc.construct_and_send_tx(inputs, output_params, priv_key)

    if not sent_tx_hash:
        err_str = f'Withdraw failed for address {from_address} and amount {withdraw_amount} ({balance} - {transaction_fee})'
        logging.error(err_str)

    return sent_tx_hash