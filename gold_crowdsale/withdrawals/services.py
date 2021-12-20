import logging
import time

import collections
from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound
from eth_account import Account

from gold_crowdsale.purchases.models import TokenPurchase
from gold_crowdsale.settings import DECIMALS, NETWORKS, ROOT_KEYS, SCHEDULER_SETTINGS
from gold_crowdsale.rates.models import UsdRate
from gold_crowdsale.crypto_api.btc import BitcoinAPI, BitcoinRPC
from gold_crowdsale.crypto_api.eth import load_w3, load_usdc_token, load_usdt_token
from gold_crowdsale.withdrawals.utils import get_private_keys


def normalize_gas_price(gas_price):
    gwei_decimals = 10 ** 9
    gas = int(round(gas_price / gwei_decimals, 0)) * gwei_decimals
    lower_gas = gas - 1 if gas > 2 else gas
    return gas, lower_gas


def withdraw_eth_funds():
    withdraw_parameters = {
        'root_private_key': ROOT_KEYS.get('private'),
        'root_public_key': ROOT_KEYS.get('public'),
        'gas_priv_key': NETWORKS.get('ETH').get('gas_privkey')
        # 'address_to_btc': get_admin_params()['WITHDRAW_ADDRESS_BTC'],
    }
    for key, value in withdraw_parameters.items():
        if not value:
            logging.error(f'Value not found for parameter {key}. Aborting')
            return

    all_purchases = TokenPurchase.objects.all().exclude(eth_address=None)
    usdc_gas_transactions = collections.defaultdict(list)
    delayed_transactions_addresses = []

    logging.info('USDC/USDT WITHDRAW (sending gas)')
    for currency in ['USDC', 'USDT']:
        for account in all_purchases:
            eth_priv_key, btc_priv_key = get_private_keys(withdraw_parameters['root_private_key'], account.id)
            logging.info(f'ETH address: {account.eth_address}')
            try:
                process_send_gas_for_usdc(withdraw_parameters, account, eth_priv_key, usdc_gas_transactions, currency)
            except Exception as e:
                logging.error(f'{currency} sending gas failed. Error is:')
                logging.error(e)

        logging.info(f'\n{currency} WITHDRAW (sending tokens)')
        try:
            parse_usdc_transactions(usdc_gas_transactions, delayed_transactions_addresses, currency)
        except Exception as e:
            logging.error(f'{currency} transaction sending failed. Error is:')
            logging.error(e)

        logging.info(f'Waiting because {currency} transactions affect ETH balance\n')
        time.sleep(SCHEDULER_SETTINGS.get('withdrawal_eth_backoff'))

    logging.info('ETH WITHDRAW')
    for account in all_purchases:
        eth_priv_key, btc_priv_key = get_private_keys(withdraw_parameters['root_private_key'], account.id)
        logging.info(f'ETH address: {account.eth_address}')
        if account.eth_address in delayed_transactions_addresses:
            logging.info('address {} skipped because of delayed gas transaction'.format(account.eth_address))
            continue
        try:
            process_withdraw_eth(account, eth_priv_key)
        except Exception as e:
            logging.error('ETH withdraw failed. Error is:')
            logging.error(e)


def process_send_gas_for_usdc(params, account, priv_key, transactions, currency):
    if currency == 'USDT':
        web3, token_contract = load_usdt_token()
    elif currency == 'USDC':
        web3, token_contract = load_usdc_token()
    else:
        logging.error(f'Cannot process sending gas: currency {currency} not supported')
        return

    gas_limit = 21000
    erc20_gas_limit = 200000
    gas_price, fake_gas_price = normalize_gas_price(web3.eth.gasPrice)
    erc20_gas_price, erc20_fake_gas_price = normalize_gas_price(web3.eth.gasPrice)
    total_gas_fee = gas_price * gas_limit
    erc20_gas_fee = erc20_gas_price * erc20_gas_limit
    rate = UsdRate.objects.get(currency='ETH')
    rate = rate.rate
    token_rate = UsdRate.objects.get(currency=currency)
    token_rate = token_rate.rate
    from_address = account.eth_address
    to_address = NETWORKS.get('ETH').get('withdraw_address')

    balance = token_contract.functions.balanceOf(web3.toChecksumAddress(from_address)).call()
    balance_check = int(((float(balance) / float(DECIMALS[currency])) * float(token_rate) / float(rate)) * float(DECIMALS['ETH']))
    eth_balance = web3.eth.getBalance(web3.toChecksumAddress(from_address))
    nonce = web3.eth.getTransactionCount(web3.toChecksumAddress(from_address), 'pending')
    gas_nonce = web3.eth.getTransactionCount(
        web3.toChecksumAddress(NETWORKS.get('ETH').get('gas_address')), 'pending')
    if balance_check <= (total_gas_fee + erc20_gas_fee):
        logging.info(f'Address {from_address} skipped: '
                     f'balance {balance_check} < tx fee of {total_gas_fee + erc20_gas_fee}')
        return

    withdraw_amount = int(balance)

    tx_params = {
        'chainId': web3.eth.chainId,
        'gas': erc20_gas_limit,
        'nonce': nonce,
        'gasPrice': erc20_fake_gas_price,
        'from': web3.toChecksumAddress(from_address),
        'to': web3.toChecksumAddress(to_address),
        'value': int(withdraw_amount),
        'priv_key': priv_key
    }

    gas_tx_params = {
        'chainId': web3.eth.chainId,
        'gas': gas_limit,
        'nonce': gas_nonce,
        'gasPrice': fake_gas_price,
        'to': web3.toChecksumAddress(from_address),
        'value': int(erc20_gas_fee * 1.2)
    }

    if eth_balance > int(erc20_gas_fee * 1.1):
        logging.info(f'Enough balance {eth_balance} > {int(erc20_gas_fee * 1.1)} '
                     f'for withdrawing {balance} from {from_address}')
        process_withdraw_usdc([tx_params], currency)
        return

    logging.info(f'send gas to {from_address}')

    signed_tx = Account.signTransaction(gas_tx_params, params['gas_priv_key'])
    try:
        sent_tx = web3.eth.sendRawTransaction(signed_tx['rawTransaction'])
        logging.info(f'sent tx: {sent_tx.hex()}')
        transactions[sent_tx.hex()].append(tx_params)
    except Exception as e:
        err_str = f'Refund failed for address {from_address} and amount {withdraw_amount} ({balance} - {total_gas_fee})'
        logging.error(err_str)
        logging.error(e)


def parse_usdc_transactions(transactions, delayed_transactions_addresses, currency):
    count = 0
    while transactions:
        if count >= 42:
            logging.info(f'Transaction receipts not found in 7 minutes.'
                         f'Supposedly they are still in pending state due to high transaction traffic or they failed, '
                         f'please check hashs {transactions.keys()} on Etherscan')
            break
        to_del = []
        for transaction in transactions.keys():
            if check_tx(transaction):
                process_withdraw_usdc(transactions[transaction], currency)
                to_del.append(transaction)
                continue
        for transaction in to_del:
            transactions.pop(transaction)
        time.sleep(10)
        count += 1
    for transaction in transactions:
        delayed_transactions_addresses.append(transactions[transaction][0]['from'].lower())


def process_withdraw_usdc(tx_params, currency):
    if currency == 'USDT':
        web3, token_contract = load_usdt_token()
    elif currency == 'USDC':
        web3, token_contract = load_usdc_token()
    else:
        logging.error(f'Cannot process sending gas: currency {currency} not supported')
        return

    priv_key = tx_params[0]['priv_key']
    from_address = tx_params[0]['from']
    to_address = tx_params[0]['to']
    value = tx_params[0]['value']
    del tx_params[0]['priv_key']
    del tx_params[0]['from']
    del tx_params[0]['to']
    del tx_params[0]['value']
    del tx_params[0]['chainId']

    logging.info('Withdraw tx params: from {} to {} on amount {}'.format(from_address, to_address, value))
    initial_tx = token_contract.functions.transfer(to_address, value).buildTransaction(tx_params[0])
    signed_tx = Account.signTransaction(initial_tx, priv_key)
    try:
        sent_tx = web3.eth.sendRawTransaction(signed_tx['rawTransaction'])
        logging.info(f'sent tx: {sent_tx.hex()}')
    except Exception as e:
        err_str = 'Refund failed for address {} and amount {})'.format(from_address, value)
        logging.info(err_str)
        logging.info(e)
    return


def process_withdraw_eth(account, priv_key):
    web3 = load_w3('ETH')

    gas_limit = 21000
    gas_price, fake_gas_price = normalize_gas_price(web3.eth.gasPrice)
    total_gas_fee = gas_price * gas_limit

    from_address = account.eth_address
    to_address = NETWORKS.get('ETH').get('withdraw_address')

    balance = web3.eth.getBalance(web3.toChecksumAddress(from_address))
    nonce = web3.eth.getTransactionCount(web3.toChecksumAddress(from_address), 'pending')

    if balance < total_gas_fee:
        logging.info(f'Address {from_address} skipped: balance {balance} < tx fee of {total_gas_fee}')
        return

    withdraw_amount = int(balance) - total_gas_fee

    tx_params = {
        'chainId': web3.eth.chainId,
        'gas': gas_limit,
        'nonce': nonce,
        'gasPrice': fake_gas_price,
        'to': web3.toChecksumAddress(to_address),
        'value': int(withdraw_amount)
    }

    logging.info(f'Withdraw tx params: from {from_address} to {to_address} on amount {withdraw_amount}')

    signed_tx = Account.signTransaction(tx_params, priv_key)
    try:
        sent_tx = web3.eth.sendRawTransaction(signed_tx['rawTransaction'])
        logging.info(f'sent tx: {sent_tx.hex()}')
    except Exception as e:
        err_str = f'Withdraw failed for address {from_address} and amount {withdraw_amount} ({balance} - {total_gas_fee})'
        logging.error(err_str)
        logging.error(e)
    return


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


def withdraw_btc_funds():
    withdraw_parameters = {
        'root_private_key': ROOT_KEYS['ETH-BTC']['private'],
        'root_public_key': ROOT_KEYS['ETH-BTC']['public'],
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
    logging.info('input_params', inputs)
    logging.info('output_params', output_params)

    sent_tx_hash = rpc.construct_and_send_tx(inputs, output_params, priv_key)

    if not sent_tx_hash:
        err_str = f'Withdraw failed for address {from_address} and amount {withdraw_amount} ({balance} - {transaction_fee})'
        logging.error(err_str)

    return sent_tx_hash


