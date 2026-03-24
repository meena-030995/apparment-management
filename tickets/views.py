# Create your views here.
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.activity_logs import log_activity
from .forms import TicketForm
from .models import Ticket
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .serializers import TicketSerializer


@login_required
def create_ticket(request):

    if request.method == "POST":

        form = TicketForm(request.POST, request.FILES)

        if form.is_valid():

            ticket = form.save(commit=False)

            ticket.resident = request.user

            ticket.save()
            log_activity(
                request.user,
                "ticket_created",
                f"Created ticket '{ticket.title}'.",
                {"ticket_id": ticket.id, "category": ticket.category},
            )

            return redirect("my_tickets")

    else:
        form = TicketForm()

    return render(request, "tickets/create_ticket.html", {"form": form})

# View Resident Tickets

@login_required
def my_tickets(request):

    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    category_filter = request.GET.get("category", "").strip()

    tickets = request.user.tickets.all().order_by("-created_at")

    if query:
        tickets = tickets.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    if status_filter:
        tickets = tickets.filter(status=status_filter)

    if category_filter:
        tickets = tickets.filter(category=category_filter)

    return render(
        request,
        "tickets/my_tickets.html",
        {
            "tickets": tickets,
            "filters": {
                "q": query,
                "status": status_filter,
                "category": category_filter,
            },
            "status_choices": Ticket.STATUS_CHOICES,
            "category_choices": Ticket.CATEGORY_CHOICES,
        }
    )
    
# Staff View All Tickets

@login_required
def all_tickets(request):

    if request.user.role not in ["staff", "admin"]:
        return redirect("dashboard")

    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    category_filter = request.GET.get("category", "").strip()
    resident_filter = request.GET.get("resident", "").strip()

    tickets = Ticket.objects.select_related("resident").order_by("-created_at")

    if query:
        tickets = tickets.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(resident__username__icontains=query)
        )

    if status_filter:
        tickets = tickets.filter(status=status_filter)

    if category_filter:
        tickets = tickets.filter(category=category_filter)

    if resident_filter:
        tickets = tickets.filter(resident__username__icontains=resident_filter)

    return render(
        request,
        "tickets/all_tickets.html",
        {
            "tickets": tickets,
            "filters": {
                "q": query,
                "status": status_filter,
                "category": category_filter,
                "resident": resident_filter,
            },
            "status_choices": Ticket.STATUS_CHOICES,
            "category_choices": Ticket.CATEGORY_CHOICES,
        }
    )
    
# Update Ticket Status (Staff)

from django.shortcuts import get_object_or_404


@login_required
def update_ticket_status(request, ticket_id):

    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.user.role not in ["staff", "admin"]:
        return redirect("dashboard")

    if request.method == "POST":

        status = request.POST.get("status")

        ticket.status = status

        ticket.save()
        log_activity(
            request.user,
            "ticket_updated",
            f"Updated ticket '{ticket.title}' to {ticket.status}.",
            {"ticket_id": ticket.id, "status": ticket.status},
        )

        return redirect("all_tickets")

    return render(
        request,
        "tickets/update_ticket.html",
        {"ticket": ticket}
    )


class TicketListAPI(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TicketSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ["staff", "admin"]:
            queryset = Ticket.objects.all()
        else:
            queryset = Ticket.objects.filter(resident=user)

        query = self.request.query_params.get("q", "").strip()
        status_filter = self.request.query_params.get("status", "").strip()
        category_filter = self.request.query_params.get("category", "").strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(resident__username__icontains=query)
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if category_filter:
            queryset = queryset.filter(category=category_filter)

        return queryset.order_by("-created_at")


class TicketCreateAPI(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TicketSerializer

    def get_queryset(self):
        return Ticket.objects.all()

    def perform_create(self, serializer):
        ticket = serializer.save(resident=self.request.user)
        log_activity(
            self.request.user,
            "ticket_created",
            f"Created ticket '{ticket.title}' via API.",
            {"ticket_id": ticket.id, "category": ticket.category},
        )


class TicketUpdateAPI(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TicketSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ["staff", "admin"]:
            return Ticket.objects.all()
        return Ticket.objects.filter(resident=user)

    def perform_update(self, serializer):
        user = self.request.user
        ticket = self.get_object()
        if user.role not in ["staff", "admin"] and ticket.resident != user:
            raise PermissionDenied("You cannot update this ticket.")
        updated_ticket = serializer.save()
        log_activity(
            user,
            "ticket_updated",
            f"Updated ticket '{updated_ticket.title}' via API.",
            {"ticket_id": updated_ticket.id, "status": updated_ticket.status},
        )


class TicketDeleteAPI(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TicketSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ["staff", "admin"]:
            return Ticket.objects.all()
        return Ticket.objects.filter(resident=user)
    
