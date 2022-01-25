import sys
import logging
import traceback
import dramatiq

from gold_crowdsale.scheduler.transfers import select_transfers
from gold_crowdsale.scheduler.withdrawals import select_withdrawals, select_withdraw_cycles
from gold_crowdsale.scheduler.queues import select_transfer_queue, select_withdraw_queue
from gold_crowdsale.settings import DEFAULT_TIME_FORMAT
from gold_crowdsale.rates.models import create_rate_obj
from gold_crowdsale.rates.serializers import UsdRateSerializer
from gold_crowdsale.transfers.models import TokenTransfer
from gold_crowdsale.withdrawals.models import TransactionManager, WithdrawTransaction, WithdrawCycle


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


@dramatiq.actor(max_retries=0)
def select_processing_withdrawals():
    select_withdrawals(
        WithdrawTransaction.Status.CREATED,
        WithdrawTransaction.Status.PENDING,
        WithdrawTransaction.Status.WAITING_FOR_ERC20_TRANSFERS,
        WithdrawTransaction.Status.WAITING_FOR_GAS_REFILL
    )


@dramatiq.actor(max_retries=0)
def select_pending_withdrawals():
    select_withdrawals(WithdrawTransaction.Status.PENDING)


@dramatiq.actor(max_retries=0)
def select_pending_withdraw_cycles():
    select_withdraw_cycles(WithdrawCycle.Status.PENDING)


@dramatiq.actor(max_retries=0)
def select_erc20_withdraw_queues():
    select_withdraw_queue(TransactionManager.QueueType.ERC20)


@dramatiq.actor(max_retries=0)
def select_gas_refill_withdraw_queues():
    select_withdraw_queue(TransactionManager.QueueType.GAS_REFILL)


@dramatiq.actor(max_retries=0)
def select_pending_transfer_queue():
    select_transfer_queue()

