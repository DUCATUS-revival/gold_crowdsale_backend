import datetime

import datetime
import dramatiq

from gold_crowdsale.settings import SCHEDULER_SETTINGS
from .models import BlockchainAccount


@dramatiq.actor
def check_and_release_accounts():
    receiving_accounts = BlockchainAccount.objects.filter(status=BlockchainAccount.Status.RECEIVING)

    for account in receiving_accounts:
        is_timeout_passed = datetime.datetime.now() > \
            account.last_updated + datetime.timedelta(seconds=SCHEDULER_SETTINGS.get('accounts_pool_timeout'))

        if is_timeout_passed:
            account.set_available()

