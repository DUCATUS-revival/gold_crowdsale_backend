from django.contrib import admin
from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from gold_crowdsale.purchases.views import TokenPurchaseView
from gold_crowdsale.rates.views import UsdRateView
from gold_crowdsale.transfers.views import FiatTransferView

schema_view = get_schema_view(
    openapi.Info(
        title="G.O.L.D. Crowdsale API",
        default_version='v1',
        description="API for G.O.L.D. Crowdsale backend",
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/purchases/', TokenPurchaseView.as_view()),
    path('api/v1/fiat-transfer/', FiatTransferView.as_view()),
    path('api/v1/usd_rates/', UsdRateView.as_view()),


]
