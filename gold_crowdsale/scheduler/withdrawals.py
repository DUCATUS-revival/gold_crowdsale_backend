import logging

from django.db import transaction, OperationalError

from gold_crowdsale.withdrawals.models import WithdrawTransaction, WithdrawCycle


def select_withdrawals(*status_list):
    withdrawals = WithdrawTransaction.objects.filter(status__in=status_list)
    for withdrawal in withdrawals:
        process_withdrawal(withdrawal.id)


def process_withdrawal(withdraw_id):
    try:
        with transaction.atomic():
            withdraw = WithdrawTransaction.objects.select_for_update(nowait=True).get(id=withdraw_id)
            if withdraw.status == WithdrawTransaction.Status.PENDING:
                withdraw.confirm_selector()
            else:
                withdraw.process_selector()

    except OperationalError as e:
        logging.error(f'PROCESS TRANSFER ERROR: failed process id {withdraw_id} with error: {e}')
        pass


def select_withdraw_cycles(*status_list):
    cycles = WithdrawCycle.objects.filter(status__in=status_list)
    for cycle in cycles:
        process_withdraw_cycles(cycle.id)


def process_withdraw_cycles(withdraw_id):
    try:
        with transaction.atomic():
            cycle = WithdrawCycle.objects.select_for_update(nowait=True).get(id=withdraw_id)
            if cycle.status == WithdrawTransaction.Status.PENDING:
                cycle.check_for_completion()

    except OperationalError as e:
        logging.error(f'PROCESS TRANSFER ERROR: failed process id {withdraw_id} with error: {e}')
        pass