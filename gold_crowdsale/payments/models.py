from django.db import models

from gold_crowdsale.settings import MAX_AMOUNT_LEN
from gold_crowdsale.purchases.models import TokenPurchase


# Create your models here.
class Payment(models.Model):
    tx_hash = models.CharField(max_length=100)
    currency = models.CharField(max_length=50)
    amount = models.CharField(max_length=MAX_AMOUNT_LEN)
    creation_datetime = models.DateTimeField(auto_now_add=True)

