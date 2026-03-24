from django.urls import path
from . import views


urlpatterns = [
    path("create/", views.create_ticket, name="create_ticket"),
    path("my/", views.my_tickets, name="my_tickets"),
    path("all/", views.all_tickets, name="all_tickets"),
    path(
        "update/<int:ticket_id>/",
        views.update_ticket_status,
        name="update_ticket"
    ),
    path("api/list/", views.TicketListAPI.as_view(), name="ticket_api_list"),
    path("api/create/", views.TicketCreateAPI.as_view(), name="ticket_api_create"),
    path("api/update/<int:pk>/", views.TicketUpdateAPI.as_view(), name="ticket_api_update"),
    path("api/delete/<int:pk>/", views.TicketDeleteAPI.as_view(), name="ticket_api_delete"),
]
