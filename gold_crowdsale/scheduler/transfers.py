import logging

from django.db import transaction, OperationalError

from gold_crowdsale.transfers.models import TokenTransfer


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