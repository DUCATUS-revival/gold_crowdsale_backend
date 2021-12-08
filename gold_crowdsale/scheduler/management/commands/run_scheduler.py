from apscheduler.schedulers.background import BlockingScheduler
from django.core.management.base import BaseCommand

from gold_crowdsale.settings import SCHEDULER_SETTINGS
from gold_crowdsale.scheduler.tasks import (
    check_and_release_accounts,
    create_rates_task,
    select_created_transfers,
    select_pending_transfers
)


class Command(BaseCommand):
    help = 'Run blocking scheduler to create periodical tasks'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Preparing scheduler'))
        scheduler = BlockingScheduler()

        accounts_interval = SCHEDULER_SETTINGS.get('accounts_task_interval')
        rates_interval = SCHEDULER_SETTINGS.get('rates_interval')
        transfer_relay_interval = SCHEDULER_SETTINGS.get('transfer_relay_interval')
        transfer_confirm_interval = SCHEDULER_SETTINGS.get('transfer_confirm_interval')
        # Accounts unblocking
        scheduler.add_job(check_and_release_accounts.send, 'interval', seconds=accounts_interval)
        # Rates updater
        scheduler.add_job(create_rates_task.send, 'interval', seconds=rates_interval)
        # Token transfer relaying
        scheduler.add_job(select_created_transfers.send, 'interval', seconds=transfer_relay_interval)
        # Token transfer confirmation
        scheduler.add_job(select_pending_transfers.send, 'interval', seconds=transfer_confirm_interval)

        self.stdout.write(self.style.NOTICE('Start scheduler'))
        scheduler.start()
