import logging
import traceback
import sys

from django.db import models

from gold_crowdsale.settings import DECIMALS, MAX_AMOUNT_LEN
from gold_crowdsale.purchases.models import TokenPurchase
from gold_crowdsale.transfers.models import create_transfer


def save_payment(token_purchase, message):
    payment = Payment(
        currency=message.get('currency'),
        amount=message.get('amount'),
        tx_hash=message.get('transactionHash'),
    )
    payment.save()

    token_purchase.payment = payment
    token_purchase.save()
    return payment


def parse_payment_message(message):
    tx_hash = message.get('transactionHash')
    if not Payment.objects.filter(tx_hash=tx_hash).count() > 0:

        token_purchase = TokenPurchase.objects.filter(
            id=message.get('exchangeId'),
            # address=message.get('address').lower()
        )
        if not token_purchase.exists():
            logging.error(f'PARSING PAYMENT ERROR: Could not find HD Wallet account {message.get("exchangeId")} '
                          f'with address {message.get("address")}, tx: {message.get("transactionHash")}'
                          f' not processed due to error')
            return
        else:
            token_purchase = token_purchase.get()

        payment = save_payment(token_purchase, message)
        logging.info(f'PARSING PAYMENT: payment {payment.tx_hash} '
                     f'for {int(payment.amount) / int(DECIMALS[payment.currency])} {payment.currency} '
                     f'successfully saved')

        create_transfer(token_purchase)

    else:
        logging.warning(f'PARSING PAYMENT: payment {tx_hash} already registered')


class Payment(models.Model):
    tx_hash = models.CharField(max_length=100)
    currency = models.CharField(max_length=50)
    amount = models.CharField(max_length=MAX_AMOUNT_LEN)
    creation_datetime = models.DateTimeField(auto_now_add=True)

