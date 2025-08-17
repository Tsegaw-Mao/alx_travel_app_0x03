from django.urls import path
from . import views
from .views import initiate_payment, verify_payment

urlpatterns = [
    path('', views.index),
    path("payments/initiate/", initiate_payment, name="initiate_payment"),
    path("payments/verify/", verify_payment, name="verify_payment"),
]
