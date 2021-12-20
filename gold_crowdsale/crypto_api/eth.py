import json
import os

from web3 import Web3, HTTPProvider

from gold_crowdsale.settings import BASE_DIR, NETWORKS


def load_w3(network):
    return Web3(HTTPProvider(NETWORKS.get(network).get('url')))


def load_w3_and_token(network, token_address):
    with open(os.path.join(BASE_DIR, 'gold_crowdsale/crypto_api/erc20_abi.json'), 'r') as erc20_file:
        erc20_abi = json.load(erc20_file)

    w3 = load_w3(network)

    gold_token_contract = w3.eth.contract(address=token_address, abi=erc20_abi)
    return w3, gold_token_contract


def load_gold_token():
    net = 'DUCX'
    return load_w3_and_token(net, NETWORKS.get(net).get('gold_token_address'))


def load_usdt_token():
    net = 'ETH'
    return load_w3_and_token(net, NETWORKS.get(net).get('usdt_token_address'))


def load_usdc_token():
    net = 'ETH'
    return load_w3_and_token(net, NETWORKS.get(net).get('usdc_token_address'))
