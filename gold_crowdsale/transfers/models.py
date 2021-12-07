import os
import sys
import json
import logging
import traceback
from web3 import Web3, HTTPProvider

from django.db import models

from gold_crowdsale.rates.models import UsdRate
from gold_crowdsale.settings import MAX_AMOUNT_LEN, BASE_DIR, RELAYING_NETWORK, DECIMALS
from gold_crowdsale.purchases.models import TokenPurchase


def load_w3_and_contract():
    with open(os.path.join(BASE_DIR, 'gold_crowdsale/erc20_abi.json'), 'r') as erc20_file:
        erc20_abi = json.load(erc20_file)

    w3 = Web3(HTTPProvider(RELAYING_NETWORK.get('url')))

    gold_token_contract = w3.eth.contract(address=RELAYING_NETWORK.get('gold_token_address'), abi=erc20_abi)
    return w3, gold_token_contract


def create_transfer(token_purchase):
    try:
        rate_object = UsdRate.objects.order_by('creation_datetime').last()
        if not rate_object:
            raise UsdRate.DoesNotExist()
    except UsdRate.DoesNotExist:
        raise Exception('CREATING TRANSFER ERROR: database does not have saved rates, check scheduler')

    usd_rate = getattr(rate_object, token_purchase.payment.currency)
    gold_rate = rate_object.GOLD
    usd_amount = int(token_purchase.payment.amount) / DECIMALS[token_purchase.payment.currency] / usd_rate
    gold_token_amount = int(usd_amount / gold_rate * DECIMALS['GOLD'])

    token_transfer = TokenTransfer(
        token_purchase=token_purchase,
        amount=gold_token_amount,
    )
    token_transfer.save()
    logging.info(f'''
       CREATING GOLD TRANSFER: {token_purchase.user_address} 
       for {int(token_transfer.amount / DECIMALS['GOLD'])} GOLD successfully created
    ''')
    return token_transfer


def parse_transfer_confirmation(message):

    transfer = TokenTransfer.objects.filter(
        id=message.get('transferId'),
        tx_hash=message.get('transactionHash')
    )

    if not transfer.exists():
        logging.error(f'''
            PARSING TRANSFER CONIFRMATION ERROR: Could not find transfer {message.get("transferId")} 
            with hash {message.get('transactionHash')} 
        ''')
        return
    else:
        transfer = transfer.get()

    transfer.validate_receipt()


class TokenTransfer(models.Model):

    class Status(models.TextChoices):
        CREATED = 'created'
        PENDING = 'pending'
        COMPLETED = 'completed'
        FAILED = 'failed'
        REVERTED = 'reverted'

    token_purchase = models.ForeignKey(TokenPurchase, on_delete=models.CASCADE, null=True, default=None)
    tx_hash = models.CharField(max_length=100, null=True)
    amount = models.DecimalField(max_digits=MAX_AMOUNT_LEN, decimal_places=0)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.CREATED)
    error_message = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_user_address(self):
        return self.token_purchase.user_address

    def send_to_user(self):
        if self.status == self.Status.COMPLETED and self.tx_hash is not None:
            logging.info(f'Token transfer already processed (tx: {self.tx_hash})')
            return

        w3, gold_token_contract = load_w3_and_contract()

        relay_tx_params = {
            'nonce': w3.eth.get_transaction_count(w3.toChecksumAddress(RELAYING_NETWORK.get('relay_address')), 'pending'),
            'gas': RELAYING_NETWORK.get('relay_gas_limit'),
            'gasPrice': RELAYING_NETWORK.get('relay_gas_price')
        }

        user_address = w3.toChecksumAddress(self.token_purchase.user_address)
        transfer_tx = gold_token_contract.functions.transfer(user_address, int(self.amount))
        built_tx = transfer_tx.buildTransaction(relay_tx_params)
        signed_tx = w3.eth.account.sign_transaction(built_tx, private_key=RELAYING_NETWORK.get('relay_privkey'))

        try:
            sent_tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
            self.status = self.Status.PENDING
        except Exception as e:
            logging.error('Could not relay token transfer tx')
            logging.error(e)
            logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))
            sent_tx_hash = None
            self.status = self.Status.FAILED
            self.error_message = e

        self.tx_hash = sent_tx_hash
        self.save()

        return sent_tx_hash

    def validate_receipt(self):
        if self.status == self.Status.COMPLETED:
            logging.info(f'Token transfer already validated (tx: {self.tx_hash})')
            return

        w3, gold_token_contract = load_w3_and_contract()

        tx_receipt = w3.eth.getTransactionReceipt(self.tx_hash)
        processed_receipt = gold_token_contract.events.Transfer().processReceipt(tx_receipt)

        if tx_receipt.get('status') == 0 or len(processed_receipt) == 0:
            self.status = self.Status.REVERTED
            logging.info(f'TRANSFER CONFIRMATION: Transfer {self.tx_hash} reverted')
        else:
            self.status = self.Status.COMPLETED
            logging.info(f'TRANSFER CONFIRMATION: Transfer {self.tx_hash} completed')

        self.save()




    # def __str__(self):
    #     if isinstance(self.tx_hash, str):
    #         return self.tx_hash
    #     return 'null'
