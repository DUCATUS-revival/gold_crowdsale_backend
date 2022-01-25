import logging

from django.db import transaction, OperationalError

from gold_crowdsale.withdrawals.models import TransactionManager, WithdrawCycle
from gold_crowdsale.transfers.models import TransferTransactionManager


def select_withdraw_queue(queue_type):
    queues = TransactionManager.objects.filter(
        queue_type=queue_type,
        withdraw_cycle__status=WithdrawCycle.Status.PENDING,
        completed=False
    )
    for queue in queues:
        process_withdraw_queue(queue.id)


def process_withdraw_queue(queue_id):
    try:
        with transaction.atomic():
            queue = TransactionManager.objects.select_for_update(nowait=True).get(id=queue_id)
            queue.set_next_tx()

    except OperationalError as e:
        logging.error(f'PROCESS WITHDRAW QUEUE ERROR: failed process id {queue_id} with error: {e}')
        pass


def select_transfer_queue():
    queue = TransferTransactionManager.objects.first()
    if not queue:
        queue = TransferTransactionManager.objects.create()
        logging.info(f'Transfer queue created, id {queue.id}')

    process_transfer_queue(queue.id)


def process_transfer_queue(queue_id):
    try:
        with transaction.atomic():
            queue = TransferTransactionManager.objects.select_for_update(nowait=True).get(id=queue_id)
            queue.set_next_tx()

    except OperationalError as e:
        logging.error(f'PROCESS TRANSFER QUEUE ERROR: failed process id {queue_id} with error: {e}')
        pass
