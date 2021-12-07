from web3 import Web3

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from gold_crowdsale.accounts.models import BlockchainAccount
from gold_crowdsale.accounts.serializers import BlockchainAccountSerializer

from .models import TokenPurchase
from .serializers import TokenPurchaseSerializer


class TokenPurchaseView(APIView):
    @swagger_auto_schema(
        operation_description="post ducx address and get addresses for payment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_address'],
            properties={
                'user_address': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={201: openapi.Response(
            description='Response with payment addresses',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'eth_address': openapi.Schema(type=openapi.TYPE_STRING),
                    'btc_address': openapi.Schema(type=openapi.TYPE_STRING),
                    'request_data:': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'user_address': openapi.Schema(type=openapi.TYPE_STRING),
                        })
                }
            )
        )},
    )
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

        payment_account_serialized = BlockchainAccountSerializer(payment_account)

        TokenPurchase.objects.create(
            user_address=user_address,
            payment_addresses=payment_account
        )

        payment_account.set_receiving()

        response_data = payment_account_serialized.data
        response_data['request_data'] = request.data

        return Response(response_data, status=status.HTTP_201_CREATED)







