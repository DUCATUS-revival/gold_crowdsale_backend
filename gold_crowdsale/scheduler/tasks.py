import sys
import logging
import traceback
import dramatiq

from django.db import transaction, OperationalError

from gold_crowdsale.settings import DEFAULT_TIME_FORMAT
from gold_crowdsale.rates.models import create_rate_obj
from gold_crowdsale.rates.serializers import UsdRateSerializer
from gold_crowdsale.transfers.models import TokenTransfer
from gold_crowdsale.withdrawals.models import WithdrawTransaction


@dramatiq.actor(max_retries=0)
def create_rates_task():
    try:
        usd_rate = create_rate_obj()
        logging.info(f'RATES TASK: Prices updated, new values: {UsdRateSerializer(usd_rate).data} '
                     f'at {usd_rate.creation_datetime.strftime(DEFAULT_TIME_FORMAT)}')
    except Exception as e:
        logging.error(f'RATES TAKS FAILED: Cannot fetch new rates because: {e}')
        logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))


@dramatiq.actor(max_retries=0)
def select_created_transfers():
    select_transfers(TokenTransfer.Status.CREATED)


@dramatiq.actor(max_retries=0)
def select_pending_transfers():
    select_transfers(TokenTransfer.Status.PENDING)


def select_transfers(*status_list):
    transfers = TokenTransfer.objects.filter(status__in=status_list)
    for transfer in transfers:
        process_transfer(transfer.id)


def process_transfer(transfer_id):
    try:
        with transaction.atomic():
            token_transfer = TokenTransfer.objects.select_for_update(nowait=True).get(id=transfer_id)
            if token_transfer.status == TokenTransfer.Status.CREATED:
                token_transfer.send_to_user()
            elif token_transfer.status == TokenTransfer.Status.PENDING:
                token_transfer.validate_receipt()

    except OperationalError as e:
        logging.error(f'PROCESS TRANSFER ERROR: failed process id {transfer_id} with error: {e}')
        pass


def process_withdrawal(withdraw_id):
    try:
        with transaction.atomic():
            withdraw = WithdrawTransaction.objects.select_for_update(nowait=True).get(id=withdraw_id)
            if withdraw.status == WithdrawTransaction.Status.CREATED:
                withdraw.process_selector()
            elif withdraw.status == WithdrawTransaction.Status.PENDING:
                withdraw.confirm_selector()

    except OperationalError as e:
        logging.error(f'PROCESS TRANSFER ERROR: failed process id {withdraw_id} with error: {e}')
        pass


def select_withdrawals(*status_list):
    withdrawals = WithdrawTransaction.objects.filter(status__in=status_list)
    for withdrawal in withdrawals:
        process_withdrawal(withdrawal.id)


@dramatiq.actor(max_retries=0)
def select_created_withdrawals():
    select_withdrawals(WithdrawTransaction.Status.CREATED)


@dramatiq.actor(max_retries=0)
def select_pending_withdrawals():
    select_withdrawals(WithdrawTransaction.Status.PENDING)
