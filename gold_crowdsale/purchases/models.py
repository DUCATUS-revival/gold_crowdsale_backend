from django.db import models

from gold_crowdsale.accounts.models import BlockchainAccount
# from gold_crowdsale.payments.models import Payment


class TokenPurchase(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending'
        COMPLETED = 'completed'
        FAILED = 'failed'

    user_address = models.CharField(max_length=100)
    payment_addresses = models.ForeignKey(BlockchainAccount, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    payment = models.OneToOneField('payments.Payment', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)

