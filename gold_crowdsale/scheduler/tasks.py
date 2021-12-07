import sys
import logging
import traceback
import datetime
import dramatiq

from gold_crowdsale.settings import SCHEDULER_SETTINGS, DEFAULT_TIME_FORMAT
from gold_crowdsale.accounts.models import BlockchainAccount
from gold_crowdsale.rates.models import UsdRate
from gold_crowdsale.rates.serializers import UsdRateSerializer


@dramatiq.actor
def check_and_release_accounts():
    receiving_accounts = BlockchainAccount.objects.filter(status=BlockchainAccount.Status.RECEIVING)

    updated_accounts = 0
    for account in receiving_accounts:
        is_timeout_passed = datetime.datetime.now() > \
            account.last_updated + datetime.timedelta(seconds=SCHEDULER_SETTINGS.get('accounts_drop_timeout'))

        if is_timeout_passed:
            account.set_available()
            updated_accounts += 1

    task_time = datetime.datetime.now().strftime(DEFAULT_TIME_FORMAT)
    logging.info(f'ACCOUNTS TASK: Receiving status dropped for {updated_accounts} accounts successfully at {task_time}')


@dramatiq.actor
def update_rates():
    rate = UsdRate.objects.first() or UsdRate()
    try:
        rate.update_rates()
        rate.save()
    except Exception as e:
        logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))

    logging.info(f'RATES TASK: Prices updated, new values: {UsdRateSerializer(rate).data} '
                 f'at {rate.last_update_datetime.strftime(DEFAULT_TIME_FORMAT)}')

