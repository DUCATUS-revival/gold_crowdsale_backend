from rest_framework import serializers

from .models import TokenPurchase


class TokenPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenPurchase
        fields = ['eth_address', 'btc_address', 'user_address']
