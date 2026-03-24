from django import forms
from .models import Visitor


class VisitorForm(forms.ModelForm):

    class Meta:
        model = Visitor

        fields = [
            "name",
            "phone",
            "flat_number",
            "vehicle_registration_number",
            "purpose"
        ]
