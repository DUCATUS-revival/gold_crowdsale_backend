from rest_framework import serializers

from .models import BlockchainAccount


class BlockchainAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockchainAccount
        fields = ['eth_address', 'btc_address']
