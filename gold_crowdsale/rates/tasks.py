import sys
import traceback
import logging
import datetime
import dramatiq

from gold_crowdsale.settings import SCHEDULER_SETTINGS
from .models import UsdRate
from .serializers import UsdRateSerializer


@dramatiq.actor
def update_rates():
    rate = UsdRate.objects.first() or UsdRate()
    try:
        rate.update_rates()
        # rate.save()
    except Exception as e:
        logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))

    logging.info(f'Prices updated, time: {str(rate.last_update_datetime)} new prices: {UsdRateSerializer(rate).data}')

