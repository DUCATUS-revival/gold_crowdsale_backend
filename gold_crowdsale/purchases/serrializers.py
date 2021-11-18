from rest_framework import serializers

from .models import TokenPurchase


class TokenPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model: TokenPurchase
        fields = ['user_address', 'payment_addresses']
