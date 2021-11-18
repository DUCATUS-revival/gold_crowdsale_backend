from web3 import Web3

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from gold_crowdsale.accounts.models import BlockchainAccount

from .models import TokenPurchase
from .serrializers import TokenPurchaseSerializer


class TokenPurchaseView(APIView):
    def post(self, request, *args, **kwargs):
        user_address = request.data.get('user_address')

        if user_address.startswith('0x'):
            try:
                Web3.toChecksumAddress(user_address)
            except:
                return Response('invalid ethereum address', status=status.HTTP_400_BAD_REQUEST)

        available_accounts = BlockchainAccount.objects.filter(status=BlockchainAccount.Status.AVAILABLE)

        if available_accounts.count() > 0:
            payment_account = available_accounts.first()
        else:
            payment_account = BlockchainAccount.objects.create()
            payment_account.save()
            payment_account.generate_keys()
            payment_account.save()

        purchase_request = TokenPurchase.objects.create(
            user_address=user_address,
            payment_addresses=payment_account
        )

        serializer = TokenPurchaseSerializer(purchase_request)

        return Response(serializer.data, status=status.HTTP_201_CREATED)







