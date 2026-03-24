# Create your views here.
import json
from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models import Q
from django.db.models.functions import TruncMonth
from .forms import FamilyMemberForm, RegisterForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.activity_logs import log_activity
from flats.models import Flat
from notices.models import Notice
from payments.models import Payment
from tickets.models import Ticket
from visitors.models import Visitor
from core.notifications import send_registration_notification
from .serializers import RegisterSerializer, UserSerializer
from .models import ActivityLog, FamilyMember, User


def home(request):
    return render(request, "home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save(commit=False)

            # Residents require approval
            if user.role == "resident":
                user.is_approved = False
            else:
                user.is_approved = True

            user.save()
            send_registration_notification(
                user,
                form.cleaned_data["password1"],
                created_at=user.date_joined,
            )

            messages.success(request, "Account created. Wait for approval.")

            return redirect('login')

        messages.error(request, "Please correct the errors below.")

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# login view
def user_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:

            if not user.is_approved:
                messages.error(request, "Account not approved by admin.")
                return redirect('login')

            login(request, user)

            return redirect('dashboard')

        else:
            messages.error(request, "Invalid credentials")

    return render(request, "accounts/login.html")

#  Logout View
def user_logout(request):
    logout(request)
    return redirect('login')

# Role Based Dashboard

@login_required
def dashboard(request):

    role = request.user.role
    context = {}

    if role == "resident":
        template = "accounts/resident_dashboard.html"
        if request.method == "POST":
            action = request.POST.get("family_action")

            if action == "delete":
                member = FamilyMember.objects.filter(
                    id=request.POST.get("member_id"),
                    resident=request.user,
                ).first()
                if member:
                    member.delete()
                    messages.success(request, "Household member removed.")
                else:
                    messages.error(request, "That household member was not found.")
                return redirect("dashboard")

            family_form = FamilyMemberForm(request.POST, resident=request.user)
            if family_form.is_valid():
                family_form.save()
                messages.success(request, "Household details saved successfully.")
                return redirect("dashboard")
            messages.error(request, "Please correct the family details form below.")
        else:
            family_form = FamilyMemberForm(resident=request.user)

        context = {
            "family_form": family_form,
            "family_members": request.user.family_members.all(),
        }

    elif role == "security":
        template = "accounts/security_dashboard.html"

    elif role == "staff":
        template = "accounts/staff_dashboard.html"
        context = {
            "resident_households": User.objects.filter(role="resident")
            .select_related("flat")
            .prefetch_related("family_members")
            .order_by("username")
        }

    else:
        template = "accounts/admin_dashboard.html"
        today = timezone.localdate()
        current_month_start = today.replace(day=1)
        six_month_window = current_month_start - timedelta(days=150)

        resident_count = User.objects.filter(role="resident").count()
        open_tickets = Ticket.objects.exclude(status="closed")
        paid_payments = Payment.objects.filter(status="paid")
        recent_tickets = Ticket.objects.select_related("resident").order_by("-created_at")[:5]
        recent_visitors = Visitor.objects.select_related("security").order_by("-entry_time")[:5]
        recent_payments = Payment.objects.select_related("resident").order_by("-created_at")[:5]

        ticket_breakdown = list(
            Ticket.objects.values("category")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        payment_trends = list(
            paid_payments.filter(created_at__date__gte=six_month_window)
            .annotate(trend_month=TruncMonth("created_at"))
            .values("trend_month")
            .annotate(total_amount=Sum("amount"))
            .order_by("trend_month")
        )

        chart_labels = [
            entry["trend_month"].strftime("%b %Y")
            for entry in payment_trends
            if entry["trend_month"] is not None
        ]
        chart_values = [
            float(entry["total_amount"] or 0)
            for entry in payment_trends
            if entry["trend_month"] is not None
        ]

        context = {
            "stats": {
                "total_residents": resident_count,
                "open_tickets": open_tickets.count(),
                "visitors_today": Visitor.objects.filter(entry_time__date=today).count(),
                "pending_payments": Payment.objects.filter(status="pending").count(),
                "occupied_flats": Flat.objects.count(),
                "active_notices": Notice.objects.filter(expiry_date__gte=today).count()
                + Notice.objects.filter(expiry_date__isnull=True).count(),
                "payments_collected": float(
                    paid_payments.aggregate(total=Sum("amount"))["total"] or 0
                ),
            },
            "recent_tickets": recent_tickets,
            "recent_visitors": recent_visitors,
            "recent_payments": recent_payments,
            "recent_activity": ActivityLog.objects.select_related("user")[:6],
            "ticket_breakdown": ticket_breakdown,
            "ticket_chart_labels": json.dumps(
                [item["category"].replace("_", " ").title() for item in ticket_breakdown]
            ),
            "ticket_chart_values": json.dumps([item["total"] for item in ticket_breakdown]),
            "payment_chart_labels": json.dumps(chart_labels),
            "payment_chart_values": json.dumps(chart_values),
            "resident_households": User.objects.filter(role="resident")
            .select_related("flat")
            .prefetch_related("family_members")
            .order_by("username"),
        }

    return render(request, template, context)


@login_required
def activity_logs(request):
    if request.user.role != "admin":
        return redirect("dashboard")

    query = request.GET.get("q", "").strip()
    action_filter = request.GET.get("action", "").strip()
    date_filter = request.GET.get("date", "").strip()

    logs = ActivityLog.objects.select_related("user").all()

    if query:
        logs = logs.filter(
            Q(user__username__icontains=query)
            | Q(description__icontains=query)
        )

    if action_filter:
        logs = logs.filter(action=action_filter)

    if date_filter:
        logs = logs.filter(created_at__date=date_filter)

    return render(
        request,
        "accounts/activity_logs.html",
        {
            "logs": logs,
            "filters": {
                "q": query,
                "action": action_filter,
                "date": date_filter,
            },
            "action_choices": ActivityLog.ACTION_CHOICES,
        },
    )


class RegisterAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_approved:
            return Response(
                {"detail": "Account not approved by admin."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        login(request, user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }
        )


class LogoutAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
