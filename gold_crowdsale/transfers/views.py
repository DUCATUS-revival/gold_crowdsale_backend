from web3 import Web3

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import create_transfer
from .serializers import FiatTokenPurchaseSerializer

class FiatTransferView(APIView):
    @swagger_auto_schema(
        operation_description="post ducx address, amount and api-key to send tokens from fiat",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_address'],
            properties={
                'user_address': openapi.Schema(type=openapi.TYPE_STRING),
                'token_amount': openapi.Schema(type=openapi.TYPE_NUMBER)
            },
        ),
        responses={"201": FiatTokenPurchaseSerializer()}
    )
    def post(self, request, *args, **kwargs):
        user_address = request.data.get('user_address')
        token_amount = request.data.get('token_amount')

        try:
            Web3.toChecksumAddress(user_address)
        except:
            return Response('invalid ethereum address', status=status.HTTP_400_BAD_REQUEST)

        if token_amount == 0:
            return Response('token amount is zero', status=status.HTTP_400_BAD_REQUEST)

        fiat_params = {
            'address_to_send': user_address,
            'token_amount': token_amount
        }

        try:
            token_transfer = create_transfer(None, True, fiat_params)
        except Exception as e:
            return Response('could not create transfer', status=status.HTTP_400_BAD_REQUEST)

        transfer_serialized = FiatTokenPurchaseSerializer(token_transfer)

        return Response(transfer_serialized.data, status=status.HTTP_201_CREATED)
