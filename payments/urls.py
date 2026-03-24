from django.urls import path
from . import views


urlpatterns = [
    path("dues/", views.my_dues, name="my_dues"),
    path("history/", views.payment_history, name="payment_history"),
    path("records/", views.payment_records, name="payment_records"),
    path("pay/<int:payment_id>/", views.pay_now, name="pay_now"),
    path("checkout/<int:payment_id>/", views.create_payment, name="create_payment"),
    path("success/", views.payment_success, name="payment_success"),
    path("api/list/", views.PaymentListAPI.as_view(), name="payment_api_list"),
    path("api/create/", views.PaymentCreateAPI.as_view(), name="payment_api_create"),
    path("api/update/<int:pk>/", views.PaymentUpdateAPI.as_view(), name="payment_api_update"),
]
