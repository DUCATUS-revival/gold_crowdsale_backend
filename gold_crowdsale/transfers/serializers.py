from rest_framework import serializers
from .models import TokenTransfer


class FiatTokenPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenTransfer
        fields = ['id', 'address_to_from_fiat', 'amount', 'status', 'created_at',  'is_fiat', 'error_message']


class FiatTxConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenTransfer
        fields = ['id', 'address_to_from_fiat', 'amount', 'status', 'created_at',  'is_fiat', 'error_message', 'tx_hash']