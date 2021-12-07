import logging
import traceback
import sys

from gold_crowdsale.settings import DECIMALS
from gold_crowdsale.accounts.models import BlockchainAccount
from gold_crowdsale.purchases.models import TokenPurchase
from gold_crowdsale.payments.models import Payment
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

        blockchain_account = BlockchainAccount.objects.filter(
            id=message.get('exchangeId'),
            # address=message.get('address').lower()
        )
        if not blockchain_account.exists():
            logging.error(f'''
                PARSING PAYMENT ERROR: Could not find HD Wallet account {message.get("exchangeId")} 
                with address {message.get("address")}, tx: {message.get("transactionHash")} not processed due to error 
            ''')
            return
        else:
            blockchain_account = blockchain_account.get()

        if blockchain_account.status != BlockchainAccount.Status.RECEIVING:
            # TODO: make autoreturn, because this account is not receiving
            return

        token_purchase = TokenPurchase.objects.filter(
            payment_addresses=blockchain_account,
            status=TokenPurchase.Status.PENDING
        )
        if not token_purchase.exists():
            logging.error(f'''
                PARSING PAYMENT ERROR: Could not find pending purchase for account with address
                {message.get("address")}, tx {message.get("transactionHash")} not processes due error'
            ''')
            return
        else:
            token_purchase = token_purchase.get()

        payment = save_payment(token_purchase, message)

        logging.info(f'''
            PARSING PAYMENT: payment {payment.tx_hash} 
            for {int(payment.amount) / int(DECIMALS[payment.currency])} {payment.currency} successfully saved
        ''')

        transfer = create_transfer(token_purchase)
        if transfer:
            try:
                # TODO: send transfers via dramatiq
                transfer.send_to_user()
                logging.info(f'TRANSFER: success sending {transfer.amount} tokens to {token_purchase.user_address}')
            except Exception:
                logging.error(f'TRANSFER ERROR: fail to send {transfer.amount} tokens to {token_purchase.user_address}')
                logging.error('error traceback:')
                logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))

    else:
        logging.warning(f'PARSING PAYMENT: payment {tx_hash} already registered')
