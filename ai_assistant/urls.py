from django.urls import path

from . import views


urlpatterns = [
    path("", views.chat_page, name="assistant_chat"),
    path("api/chat/", views.chat_api, name="assistant_chat_api"),
]
