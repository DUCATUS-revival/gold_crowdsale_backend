from apscheduler.schedulers.background import BlockingScheduler
from django.core.management.base import BaseCommand

from gold_crowdsale.settings import SCHEDULER_SETTINGS, FIAT_ONLY_MODE
from gold_crowdsale.scheduler.tasks import (
    create_rates_task,
    select_created_transfers,
    select_pending_transfers,
    select_processing_withdrawals,
    select_pending_withdrawals,
    select_pending_withdraw_cycles,
    select_pending_transfer_queue,
    select_erc20_withdraw_queues,
    select_gas_refill_withdraw_queues
)


class Command(BaseCommand):
    help = 'Run blocking scheduler to create periodical tasks'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Preparing scheduler'))
        scheduler = BlockingScheduler()

        transfer_relay_interval = SCHEDULER_SETTINGS.get('transfer_relay_interval')
        transfer_confirm_interval = SCHEDULER_SETTINGS.get('transfer_confirm_interval')
        queues_polling_interval = SCHEDULER_SETTINGS.get('queues_polling_interval')

        # Token transfer relaying
        scheduler.add_job(select_created_transfers.send, 'interval', seconds=transfer_relay_interval)
        # Token transfer confirmation
        scheduler.add_job(select_pending_transfers.send, 'interval', seconds=transfer_confirm_interval)
        # Job for handling network queue for token transfers
        scheduler.add_job(select_pending_transfer_queue.send, 'interval', seconds=queues_polling_interval)

        if not FIAT_ONLY_MODE:
            rates_interval = SCHEDULER_SETTINGS.get('rates_interval')
            withdrawals_polling_interval = SCHEDULER_SETTINGS.get('withdrawals_polling_interval')
            withdrawal_cycles_polling_interval = SCHEDULER_SETTINGS.get('withdrawal_cycles_polling_interval')
            withdrawals_confirm_interval = SCHEDULER_SETTINGS.get('withdrawals_confirm_interval')
            # Rates updater
            scheduler.add_job(create_rates_task.send, 'interval', seconds=rates_interval)
            # Withdraw creation
            scheduler.add_job(select_processing_withdrawals.send, 'interval', seconds=withdrawals_polling_interval)
            # Withdraw confirmation
            scheduler.add_job(select_pending_withdrawals.send, 'interval', seconds=withdrawals_confirm_interval)
            # Job to check if all withdraw transactions on cycle is processed
            scheduler.add_job(select_pending_withdraw_cycles.send, 'interval', seconds=withdrawal_cycles_polling_interval)
            # Job for handling account queue on ERC20 withdrawals
            scheduler.add_job(select_erc20_withdraw_queues.send, 'interval', seconds=queues_polling_interval)
            # Job for handling glocal withdraw queue on gas refills
            scheduler.add_job(select_gas_refill_withdraw_queues.send, 'interval', seconds=queues_polling_interval)

        self.stdout.write(self.style.NOTICE('Start scheduler'))
        scheduler.start()
