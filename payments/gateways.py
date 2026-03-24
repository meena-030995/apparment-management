from decimal import Decimal

from django.conf import settings
from django.urls import reverse


class PaymentGatewayError(Exception):
    pass


class RazorpayGateway:
    provider = "razorpay"
    label = "Razorpay"

    def create_checkout(self, payment, request):
        try:
            import razorpay
        except ImportError as exc:
            raise PaymentGatewayError("Razorpay SDK is not installed.") from exc

        key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
        key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
        if not key_id or not key_secret:
            raise PaymentGatewayError("Razorpay keys are not configured.")

        client = razorpay.Client(auth=(key_id, key_secret))
        order = client.order.create(
            {
                "amount": int(Decimal(payment.amount) * 100),
                "currency": "INR",
                "payment_capture": "1",
            }
        )

        payment.gateway = self.provider
        payment.gateway_order_id = order["id"]
        payment.save(update_fields=["gateway", "gateway_order_id"])

        return {
            "mode": "razorpay",
            "provider_label": self.label,
            "public_key": key_id,
            "order_id": order["id"],
            "amount_paise": int(Decimal(payment.amount) * 100),
            "display_name": getattr(settings, "APARTMENT_NAME", "AMS Apartment"),
        }


class StripeGateway:
    provider = "stripe"
    label = "Stripe"

    def create_checkout(self, payment, request):
        try:
            import stripe
        except ImportError as exc:
            raise PaymentGatewayError("Stripe SDK is not installed.") from exc

        secret_key = getattr(settings, "STRIPE_SECRET_KEY", "")
        if not secret_key:
            raise PaymentGatewayError("Stripe keys are not configured.")

        stripe.api_key = secret_key
        success_url = request.build_absolute_uri(reverse("payment_success"))
        success_url = f"{success_url}?payment_id={payment.id}&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.build_absolute_uri(reverse("my_dues"))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "product_data": {
                            "name": f"{payment.get_payment_type_display()} due",
                        },
                        "unit_amount": int(Decimal(payment.amount) * 100),
                    },
                    "quantity": 1,
                }
            ],
        )

        payment.gateway = self.provider
        payment.gateway_order_id = session.id
        payment.save(update_fields=["gateway", "gateway_order_id"])

        return {
            "mode": "redirect",
            "provider_label": self.label,
            "checkout_url": session.url,
        }


def get_payment_gateway(provider_name):
    gateways = {
        "razorpay": RazorpayGateway,
        "stripe": StripeGateway,
    }
    gateway_class = gateways.get(provider_name)
    if gateway_class is None:
        raise PaymentGatewayError(f"Unsupported gateway '{provider_name}'.")
    return gateway_class()
