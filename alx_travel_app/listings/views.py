from rest_framework import viewsets, status
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer
import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


CHAPA_HEADERS = {
    "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
    "Content-Type": "application/json"
}

@api_view(["POST"])
def initiate_payment(request):
    booking_reference = request.data.get("booking_reference")
    amount = request.data.get("amount")
    email = request.data.get("email")

    if not booking_reference or not amount or not email:
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "email": email,
        "tx_ref": booking_reference,
        "callback_url": "http://localhost:8000/api/payments/verify/"
    }

    response = requests.post(f"{settings.CHAPA_BASE_URL}/transaction/initialize", json=payload, headers=CHAPA_HEADERS)

    if response.status_code == 200:
        data = response.json()
        transaction_id = data["data"]["tx_ref"]
        payment = Payment.objects.create(
            booking_reference=booking_reference,
            amount=amount,
            transaction_id=transaction_id,
            status="Pending"
        )
        return Response({"payment_url": data["data"]["checkout_url"], "transaction_id": transaction_id})
    else:
        return Response({"error": "Failed to initiate payment"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def verify_payment(request):
    transaction_id = request.query_params.get("transaction_id")

    if not transaction_id:
        return Response({"error": "Transaction ID required"}, status=status.HTTP_400_BAD_REQUEST)

    response = requests.get(f"{settings.CHAPA_BASE_URL}/transaction/verify/{transaction_id}", headers=CHAPA_HEADERS)

    if response.status_code == 200:
        data = response.json()
        payment = Payment.objects.filter(transaction_id=transaction_id).first()

        if not payment:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if data["status"] == "success" and data["data"]["status"] == "success":
            payment.status = "Completed"
            payment.save()
            # TODO: Trigger Celery task to send confirmation email
            return Response({"message": "Payment successful", "status": payment.status})
        else:
            payment.status = "Failed"
            payment.save()
            return Response({"message": "Payment failed", "status": payment.status})
    else:
        return Response({"error": "Verification failed"}, status=status.HTTP_400_BAD_REQUEST)
