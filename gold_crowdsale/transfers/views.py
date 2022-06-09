import sys
import traceback
import logging
from web3 import Web3

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from gold_crowdsale.api_auth.permissions import HasAPIKey

from .models import create_transfer, TokenTransfer
from .serializers import FiatTokenPurchaseSerializer, FiatTxConfirmationSerializer


class FiatTransferView(APIView):
    permission_classes = [HasAPIKey]

    @swagger_auto_schema(
        operation_description="post ducx address, amount and api-key to send tokens from fiat",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_address', 'token_amount', 'api_key'],
            properties={
                'user_address': openapi.Schema(type=openapi.TYPE_STRING),
                'token_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING)
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
            return Response(
                {'error': 'invalid ethereum address'},
                status=status.HTTP_400_BAD_REQUEST)

        if token_amount == 0:
            return Response(
                {'error': 'token amount is zero'},
                status=status.HTTP_400_BAD_REQUEST)

        fiat_params = {
            'address_to_send': user_address,
            'token_amount': token_amount
        }

        try:
            token_transfer = create_transfer(None, True, fiat_params)
        except Exception as e:
            logging.error(f'Could not create transfer because: {e}')
            logging.error('\n'.join(traceback.format_exception(*sys.exc_info())))
            return Response(
                {'error': 'could not create transfer'},
                status=status.HTTP_400_BAD_REQUEST)

        transfer_serialized = FiatTokenPurchaseSerializer(token_transfer)

        return Response(transfer_serialized.data, status=status.HTTP_201_CREATED)

class FiatTransferTransactionsList(ListAPIView):
    permission_classes = [HasAPIKey]
    queryset = TokenTransfer.objects.filter(is_fiat=True)
    serializer_class = FiatTxConfirmationSerializer

    @swagger_auto_schema(
        operation_description="retrieve all fiat transfers in list",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['api_key'],
            properties={
                'api_key': openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={"200": FiatTxConfirmationSerializer()}
    )
    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        pass

class FiatTransferTransaction(RetrieveAPIView):
    permission_classes = [HasAPIKey]
    queryset = TokenTransfer.objects.filter(is_fiat=True)
    serializer_class = FiatTxConfirmationSerializer
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_description="get fiat transfer info by id",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['api_key'],
            properties={
                'api_key': openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={"200": FiatTxConfirmationSerializer()}
    )
    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, *args, **kwargs):
        pass

