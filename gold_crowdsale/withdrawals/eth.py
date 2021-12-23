import sys
import traceback
import logging
import time

import collections

from eth_account import Account

from gold_crowdsale.purchases.models import TokenPurchase
from gold_crowdsale.settings import DECIMALS, NETWORKS, ROOT_KEYS, SCHEDULER_SETTINGS
from gold_crowdsale.rates.models import get_rate_object
from gold_crowdsale.crypto_api.eth import load_w3, load_eth_erc20_token
from gold_crowdsale.withdrawals.utils import get_private_keys






def parse_erc20_transactions(transactions, delayed_transactions_addresses, currency):
    try:
        count = 0
        while transactions:
            if count >= 42:
                logging.info(f'Transaction receipts not found in 7 minutes.'
                             f'Supposedly they are still in pending state due to high '
                             f'transaction traffic or they failed, '
                             f'please check hashs {transactions.keys()} on Etherscan')
                break
            to_del = []
            for transaction in transactions.keys():
                if check_tx(transaction):
                    process_withdraw_erc20(transactions[transaction], currency)
                    to_del.append(transaction)
                    continue
            for transaction in to_del:
                transactions.pop(transaction)
            time.sleep(10)
            count += 1
        for transaction in transactions:
            delayed_transactions_addresses.append(transactions[transaction][0]['from'].lower())
    except Exception as e:
        logging.error(f'{currency} transaction sending failed. Error is: {e}')
        logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))


def withdraw_eth_funds():
    withdraw_parameters = {
        'root_private_key': ROOT_KEYS.get('private'),
        'root_public_key': ROOT_KEYS.get('public'),
        'gas_priv_key': NETWORKS.get('ETH').get('gas_privkey')
    }
    for key, value in withdraw_parameters.items():
        if not value:
            logging.error(f'Value not found for parameter {key}. Aborting')
            return

    all_purchases = TokenPurchase.objects.all().exclude(eth_address=None)
    erc20_gas_transactions = collections.defaultdict(list)
    delayed_transactions_addresses = []

    for currency in ['USDC', 'USDT']:
        logging.info(f'{currency} WITHDRAW (sending gas)')
        for account in all_purchases:
            process_send_gas_for_erc20(withdraw_parameters, account, erc20_gas_transactions, currency)

        logging.info(f'\n{currency} WITHDRAW (sending tokens)')
        parse_erc20_transactions(erc20_gas_transactions, delayed_transactions_addresses, currency)

        if len(erc20_gas_transactions) > 0:
            logging.info(f'Waiting because {currency} transactions affect ETH balance\n')
            time.sleep(SCHEDULER_SETTINGS.get('withdrawal_eth_backoff'))
        else:
            logging.info(f'no gas sending transactions for ERC20 token {currency}, ETH balance should be unaffected')

    logging.info('ETH WITHDRAW')
    for account in all_purchases:
        process_withdraw_eth(withdraw_parameters, account, delayed_transactions_addresses)
