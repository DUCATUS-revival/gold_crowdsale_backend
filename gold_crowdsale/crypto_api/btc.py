import sys
import json
import time
import requests
import logging
import traceback

from bitcoinrpc.authproxy import AuthServiceProxy

from gold_crowdsale.settings import NETWORKS, DECIMALS


class BitcoinRPC:
    def __init__(self):
        self.endpoint = None
        self.connection = None
        self.network_info = None
        self.version = None
        self.relay_fee = None
        self.establish_connection()

    def setup_endpoint(self):
        self.endpoint = 'http://{user}:{pwd}@{host}:{port}'.format(
            user=NETWORKS.get('BTC').get('user'),
            pwd=NETWORKS.get('BTC').get('password'),
            host=NETWORKS.get('BTC').get('host'),
            port=NETWORKS.get('BTC').get('port'),
        )
        return

    def establish_connection(self):
        self.setup_endpoint()
        self.connection = AuthServiceProxy(self.endpoint)
        self.network_info = self.connection.getnetworkinfo()
        self.version = int(str(self.network_info['version'])[:2])
        res = requests.get('https://api.bitcore.io/api/BTC/mainnet/fee/100')
        self.relay_fee = int(json.loads(res.text)['feerate'] * DECIMALS['BTC'])

    def reconnect(self):
        self.establish_connection()

    def create_raw_transaction(self, input_params, output_params):
        self.reconnect()
        return self.connection.createrawtransaction(input_params, output_params)

    def sign_raw_transaction(self, tx, private_key):
        self.reconnect()
        if self.version >= 17:
            return self.connection.signrawtransactionwithkey(tx, [private_key])
        else:
            return self.connection.signrawtransaction(tx, None, [private_key])

    def send_raw_transaction(self, tx_hex):
        self.reconnect()
        return self.connection.sendrawtransaction(tx_hex)

    def construct_and_send_tx(self, input_params, output_params, private_key):
        tx = self.create_raw_transaction(input_params, output_params)

        signed = self.sign_raw_transaction(tx, private_key)

        try:
            tx_hash = self.send_raw_transaction(signed['hex'])
            logging.info(f'tx: {tx_hash}')
            return tx_hash, True
        except Exception as e:
            logging.error(f'FAILED SENDING TRANSACTION: {e}')
            logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))
            return e, False

    def validateaddress(self, address):
        self.reconnect()
        return self.connection.validateaddress(address)


class BitcoinAPI:
    def __init__(self):
        self.network = 'testnet'
        if 'is_mainnet' in NETWORKS.get('BTC'):
            if NETWORKS.get('BTC').get('is_mainnet'):
                self.network = 'mainnet'

        self.base_url = None
        self.set_base_url()

    def set_base_url(self):
        self.base_url = f'https://api.bitcore.io/api/BTC/{self.network}'

    def get_address_response(self, address):
        endpoint_url = f'{self.base_url}/address/{address}'
        res = requests.get(endpoint_url)
        if not res.ok:
            return [], False
        else:
            valid_json = len(res.json()) > 0
            if not valid_json:
                logging.info('Address have no transactions and balance is 0')
                return [], True

            return res.json(), True

    def get_address_unspent_all(self, address):
        inputs_of_address, response_ok = self.get_address_response(address)
        if not response_ok:
            return [], 0, False

        if response_ok and len(inputs_of_address) == 0:
            return inputs_of_address, 0, True

        inputs_value = 0
        unspent_inputs = []
        for input_tx in inputs_of_address:
            if not input_tx['spentTxid']:
                unspent_inputs.append({
                    'txid': input_tx['mintTxid'],
                    'vout': input_tx['mintIndex']
                })
                inputs_value += input_tx['value']

        return unspent_inputs, inputs_value, True

    def get_address_unspent_from_tx(self, address, tx_hash):
        inputs_of_address, response_ok = self.get_address_response(address)
        if not response_ok:
            return [], 0, False

        if response_ok and len(inputs_of_address) == 0:
            return inputs_of_address, 0, True

        # find vout
        vout = None
        input_value = 0
        for input_tx in inputs_of_address:
            if not input_tx['spentTxid'] and input_tx['mintTxid'] == tx_hash:
                vout = input_tx['mintIndex']
                input_value = input_tx['value']

        if vout is None:
            return [], 0, False

        input_params = [{'txid': tx_hash, 'vout': vout}]
        return input_params, input_value, True

    def get_return_address(self, tx_hash):
        endpoint_url = f'{self.base_url}/tx/{tx_hash}/coins'
        res = requests.get(endpoint_url)
        if not res.ok:
            return '', False
        else:
            tx_info = res.json()

        inputs_of_tx = tx_info['inputs']
        if len(inputs_of_tx) == 0:
            return '', False

        first_input = inputs_of_tx[0]
        return_address = first_input['address']

        address_found = False
        if return_address:
            address_found = True

        return return_address, address_found

    def get_tx_confirmations(self, tx_hash):
        endpoint_url = f'{self.base_url}/tx/{tx_hash}'
        res = requests.get(endpoint_url)
        if not res.ok:
            return '', False
        else:
            tx_info = res.json()

        confirmations = tx_info.get('confirmations')
        return confirmations

