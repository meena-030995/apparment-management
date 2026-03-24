from django import forms
from .models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = [
            "title",
            "message",
            "document",
            "expiry_date"
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "document": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "expiry_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }
