from django import forms

from accounts.models import User

from .models import Payment


class PaymentRecordForm(forms.ModelForm):
    resident = forms.ModelChoiceField(
        queryset=User.objects.filter(role="resident").order_by("username"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Payment
        fields = [
            "resident",
            "month",
            "year",
            "due_date",
            "payment_type",
            "amount",
            "status",
            "gateway",
            "payment_method",
            "transaction_id",
        ]
        widgets = {
            "month": forms.TextInput(attrs={"class": "form-control", "placeholder": "March"}),
            "year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "2026"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "payment_type": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "gateway": forms.Select(attrs={"class": "form-select"}),
            "payment_method": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "UPI, Card, Net Banking, Manual"}
            ),
            "transaction_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Optional transaction ID"}
            ),
        }
