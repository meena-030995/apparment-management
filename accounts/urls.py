from django.urls import path
from . import views


urlpatterns = [

    path('', views.home, name="home"),
    path('register/', views.register, name="register"),
    path('login/', views.user_login, name="login"),
    path('logout/', views.user_logout, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('activity-logs/', views.activity_logs, name="activity_logs"),
    path("api/register/", views.RegisterAPI.as_view(), name="api_register"),
    path("api/login/", views.LoginAPI.as_view(), name="api_login"),
    path("api/logout/", views.LogoutAPI.as_view(), name="api_logout"),
    path("api/me/", views.CurrentUserAPI.as_view(), name="api_me"),

]
