# from django.shortcuts import render

# Create your views here.
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.activity_logs import log_activity
from .forms import VisitorForm
from .models import Visitor
from django.contrib import messages
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics, permissions

from .serializers import VisitorSerializer


@login_required
def add_visitor(request):

    if request.user.role != "security":
        messages.error(request, "Only security can add visitor entries.")
        return redirect("dashboard")

    if request.method == "POST":

        form = VisitorForm(request.POST)

        if form.is_valid():

            visitor = form.save(commit=False)

            visitor.security = request.user

            visitor.save()
            log_activity(
                request.user,
                "visitor_added",
                f"Added visitor '{visitor.name}' for flat {visitor.flat_number}.",
                {
                    "visitor_id": visitor.id,
                    "flat_number": visitor.flat_number,
                    "vehicle_registration_number": visitor.vehicle_registration_number,
                },
            )

            return redirect("visitor_list")

    else:
        form = VisitorForm()

    return render(request, "visitors/add_visitor.html", {"form": form})

@login_required
def visitor_list(request):

    if request.user.role not in ["security", "admin", "staff"]:
        
        return redirect("dashboard")

    query = request.GET.get("q", "").strip()
    flat_filter = request.GET.get("flat", "").strip()
    date_filter = request.GET.get("date", "").strip()
    exit_filter = request.GET.get("exit_status", "").strip()

    visitors = Visitor.objects.select_related("security").order_by("-entry_time")

    if query:
            visitors = visitors.filter(
                Q(name__icontains=query)
                | Q(phone__icontains=query)
                | Q(flat_number__icontains=query)
                | Q(vehicle_registration_number__icontains=query)
                | Q(purpose__icontains=query)
            )

    if flat_filter:
        visitors = visitors.filter(flat_number__icontains=flat_filter)

    if date_filter:
        visitors = visitors.filter(entry_time__date=date_filter)

    if exit_filter == "pending":
        visitors = visitors.filter(exit_time__isnull=True)
    elif exit_filter == "completed":
        visitors = visitors.filter(exit_time__isnull=False)

    return render(
        request,
        "visitors/visitor_list.html",
        {
            "visitors": visitors,
            "filters": {
                "q": query,
                "flat": flat_filter,
                "date": date_filter,
                "exit_status": exit_filter,
            },
        }
    )

from django.shortcuts import get_object_or_404
from django.utils import timezone


@login_required
def visitor_exit(request, visitor_id):

    if request.user.role not in ["security", "admin"]:
        messages.error(request, "Only security staff can update visitor exit.")
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("visitor_list")

    visitor = get_object_or_404(Visitor, id=visitor_id)

    visitor.exit_time = timezone.now()

    visitor.save()
    log_activity(
        request.user,
        "visitor_exited",
        f"Marked exit for visitor '{visitor.name}'.",
        {"visitor_id": visitor.id, "flat_number": visitor.flat_number},
    )

    return redirect("visitor_list")


class VisitorListAPI(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VisitorSerializer

    def get_queryset(self):
        if self.request.user.role in ["security", "admin", "staff"]:
            queryset = Visitor.objects.all()
            query = self.request.query_params.get("q", "").strip()
            flat_filter = self.request.query_params.get("flat", "").strip()
            date_filter = self.request.query_params.get("date", "").strip()
            exit_filter = self.request.query_params.get("exit_status", "").strip()

            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query)
                    | Q(phone__icontains=query)
                    | Q(flat_number__icontains=query)
                    | Q(purpose__icontains=query)
                )

            if flat_filter:
                queryset = queryset.filter(flat_number__icontains=flat_filter)

            if date_filter:
                queryset = queryset.filter(entry_time__date=date_filter)

            if exit_filter == "pending":
                queryset = queryset.filter(exit_time__isnull=True)
            elif exit_filter == "completed":
                queryset = queryset.filter(exit_time__isnull=False)

            return queryset.order_by("-entry_time")
        return Visitor.objects.none()


class VisitorCreateAPI(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VisitorSerializer

    def get_queryset(self):
        return Visitor.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role != "security":
            raise PermissionDenied("Only security can add visitors.")
        visitor = serializer.save(security=self.request.user)
        log_activity(
            self.request.user,
            "visitor_added",
            f"Added visitor '{visitor.name}' via API.",
            {
                "visitor_id": visitor.id,
                "flat_number": visitor.flat_number,
                "vehicle_registration_number": visitor.vehicle_registration_number,
            },
        )
