from django.urls import path
from . import views


urlpatterns = [
    path("add/", views.add_visitor, name="add_visitor"),
    path("list/", views.visitor_list, name="visitor_list"),
    path(
        "exit/<int:visitor_id>/",
        views.visitor_exit,
        name="visitor_exit"
    ),
    path("api/list/", views.VisitorListAPI.as_view(), name="visitor_api_list"),
    path("api/create/", views.VisitorCreateAPI.as_view(), name="visitor_api_create"),
]
