from web3 import Web3

from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


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
        responses={201: TokenPurchaseSerializer()}
    )
    def post(self, request, *args, **kwargs):
        user_address = request.data.get('user_address')

        try:
            Web3.toChecksumAddress(user_address)
        except:
            return Response(
                {'error': 'invalid ducatusx address'},
                status=status.HTTP_400_BAD_REQUEST)

        token_purchase, purchase_created = TokenPurchase.objects.get_or_create(user_address=user_address)

        if purchase_created:
            token_purchase.save()
            token_purchase.generate_keys()

        purchase_serialized = TokenPurchaseSerializer(token_purchase)

        return Response(purchase_serialized.data, status=status.HTTP_201_CREATED)
