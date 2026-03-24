from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.activity_logs import log_activity
from .models import Payment
from django.contrib import messages
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics, permissions

from .forms import PaymentRecordForm
from .gateways import PaymentGatewayError, get_payment_gateway
from .serializers import PaymentSerializer


@login_required
def my_dues(request):
    payments = Payment.objects.filter(resident=request.user).order_by("status", "due_date", "-created_at")

    return render(
        request,
        "payments/my_dues.html",
        {"payments": payments}
    )

@login_required
def payment_history(request):

    payments = Payment.objects.filter(
        resident=request.user,
        status="paid"
    ).order_by("-created_at")

    return render(
        request,
        "payments/payment_history.html",
        {"payments": payments}
    )


@login_required
def payment_records(request):
    if request.user.role != "admin":
        return redirect("dashboard")

    edit_payment = None
    edit_payment_id = request.GET.get("edit")
    if edit_payment_id:
        edit_payment = get_object_or_404(Payment, pk=edit_payment_id)

    if request.method == "POST":
        action = request.POST.get("action", "create")
        if action == "update":
            edit_payment = get_object_or_404(Payment, pk=request.POST.get("payment_id"))
            previous_status = edit_payment.status
            form = PaymentRecordForm(request.POST, instance=edit_payment)
        else:
            previous_status = None
            form = PaymentRecordForm(request.POST)
        if form.is_valid():
            payment = form.save()
            if action == "update":
                if previous_status != payment.status:
                    log_activity(
                        request.user,
                        "payment_paid" if payment.status == "paid" else "payment_created",
                        f"Updated payment record for {payment.resident.username} to {payment.status}.",
                        {"payment_id": payment.id, "amount": float(payment.amount)},
                    )
                messages.success(request, "Payment record updated successfully.")
            else:
                log_activity(
                    request.user,
                    "payment_created",
                    f"Created payment record for {payment.resident.username}.",
                    {"payment_id": payment.id, "amount": float(payment.amount)},
                )
                messages.success(request, "Payment record created successfully.")
            return redirect("payment_records")
        messages.error(request, "Please correct the payment form errors below.")
    else:
        form = PaymentRecordForm(instance=edit_payment) if edit_payment else PaymentRecordForm()

    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    month_filter = request.GET.get("month", "").strip()
    year_filter = request.GET.get("year", "").strip()

    payments = Payment.objects.select_related("resident").order_by("-created_at")

    if query:
        payments = payments.filter(
            Q(resident__username__icontains=query)
            | Q(transaction_id__icontains=query)
            | Q(month__icontains=query)
        )

    if status_filter:
        payments = payments.filter(status=status_filter)

    if month_filter:
        payments = payments.filter(month__icontains=month_filter)

    if year_filter:
        payments = payments.filter(year=year_filter)

    context = {
        "payments": payments,
        "pending_count": payments.filter(status="pending").count(),
        "paid_count": payments.filter(status="paid").count(),
        "filters": {
            "q": query,
            "status": status_filter,
            "month": month_filter,
            "year": year_filter,
        },
        "status_choices": Payment.STATUS_CHOICES,
        "form": form,
        "edit_payment": edit_payment,
    }

    return render(request, "payments/payment_records.html", context)

import uuid
from django.shortcuts import redirect, get_object_or_404


@login_required
def pay_now(request, payment_id):

    if request.method != "POST":
        return redirect("my_dues")

    payment = get_object_or_404(
        Payment,
        id=payment_id,
        resident=request.user,
        status="pending",
    )

    payment.status = "paid"

    payment.transaction_id = str(uuid.uuid4())

    payment.save()
    log_activity(
        request.user,
        "payment_paid",
        f"Completed payment for {payment.month} {payment.year}.",
        {"payment_id": payment.id, "amount": float(payment.amount)},
    )

    return redirect("payment_history")


@login_required
def create_payment(request, payment_id):
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        resident=request.user,
        status="pending",
    )

    try:
        checkout = get_payment_gateway(payment.gateway).create_checkout(payment, request)
    except PaymentGatewayError as exc:
        if settings.DEBUG:
            messages.warning(
                request,
                (
                    f"{exc} Running in development mode, so a test checkout "
                    "has been enabled for this payment."
                ),
            )
            checkout = {
                "mode": "manual_fallback",
                "provider_label": "Development Checkout",
            }
            return render(
                request,
                "payments/pay.html",
                {"payment": payment, "checkout": checkout},
            )
        messages.error(request, str(exc))
        return redirect("my_dues")

    if checkout["mode"] == "redirect":
        return redirect(checkout["checkout_url"])

    context = {
        "payment": payment,
        "checkout": checkout,
    }

    return render(request, "payments/pay.html", context)

@login_required
def payment_success(request):
    if request.method == "POST":
        payment = get_object_or_404(
            Payment,
            id=request.POST.get("payment_id"),
            resident=request.user,
            status="pending",
        )

        payment.status = "paid"
        payment.transaction_id = request.POST.get("razorpay_payment_id")
        payment.payment_method = "Razorpay"
        payment.gateway = "razorpay"
        payment.save()
        log_activity(
            request.user,
            "payment_paid",
            f"Completed Razorpay payment for {payment.month} {payment.year}.",
            {"payment_id": payment.id, "amount": float(payment.amount)},
        )
        return redirect("payment_history")

    session_id = request.GET.get("session_id")
    payment = get_object_or_404(
        Payment,
        id=request.GET.get("payment_id"),
        resident=request.user,
        status="pending",
    )

    if payment.gateway != "stripe" or not session_id:
        return redirect("my_dues")

    try:
        import stripe
    except ImportError:
        messages.error(request, "Stripe SDK is not installed.")
        return redirect("my_dues")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        messages.error(request, "Stripe is not configured.")
        return redirect("my_dues")

    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status != "paid":
        messages.error(request, "Stripe payment is not completed yet.")
        return redirect("my_dues")

    payment.status = "paid"
    payment.transaction_id = session.payment_intent or session.id
    payment.payment_method = "Stripe Checkout"
    payment.save()
    log_activity(
        request.user,
        "payment_paid",
        f"Completed Stripe payment for {payment.month} {payment.year}.",
        {"payment_id": payment.id, "amount": float(payment.amount)},
    )
    return redirect("payment_history")


class PaymentListAPI(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            queryset = Payment.objects.all()
        else:
            queryset = Payment.objects.filter(resident=user)

        query = self.request.query_params.get("q", "").strip()
        status_filter = self.request.query_params.get("status", "").strip()
        month_filter = self.request.query_params.get("month", "").strip()
        year_filter = self.request.query_params.get("year", "").strip()

        if query:
            queryset = queryset.filter(
                Q(resident__username__icontains=query)
                | Q(transaction_id__icontains=query)
                | Q(month__icontains=query)
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if month_filter:
            queryset = queryset.filter(month__icontains=month_filter)

        if year_filter:
            queryset = queryset.filter(year=year_filter)

        return queryset.order_by("-created_at")


class PaymentCreateAPI(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admin can create payments.")
        payment = serializer.save()
        log_activity(
            self.request.user,
            "payment_created",
            f"Created payment record for {payment.resident.username}.",
            {"payment_id": payment.id, "amount": float(payment.amount)},
        )


class PaymentUpdateAPI(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        if self.request.user.role == "admin":
            return Payment.objects.all()
        return Payment.objects.filter(resident=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admin can update payments.")
        previous_status = self.get_object().status
        payment = serializer.save()
        if previous_status != payment.status:
            log_activity(
                self.request.user,
                "payment_paid" if payment.status == "paid" else "payment_created",
                f"Updated payment record for {payment.resident.username} to {payment.status}.",
                {"payment_id": payment.id, "amount": float(payment.amount)},
            )
