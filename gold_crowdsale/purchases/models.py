from django.db import models

from gold_crowdsale.accounts.models import BlockchainAccount


class TokenPurchase(models.Model):
    user_address = models.CharField(max_length=100)
    payment_addresses = models.ForeignKey(BlockchainAccount, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


