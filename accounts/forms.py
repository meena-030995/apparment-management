from django import forms
from django.contrib.auth.forms import UserCreationForm

from flats.models import Block, Flat

from .models import FamilyMember, User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "register-input"}))
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "register-input"}))
    phone = forms.CharField(widget=forms.TextInput(attrs={"class": "register-input"}))
    block = forms.ModelChoiceField(
        queryset=Block.objects.all(),
        required=False,
        empty_label="Select block",
        widget=forms.Select(attrs={"class": "register-input register-select"}),
    )
    flat_number = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={"class": "register-input"}),
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "register-input register-select"}),
    )
    id_proof = forms.FileField(required=False)
    address_proof = forms.FileField(required=False)
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "register-input"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "register-input"})
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone',
            'block',
            'flat_number',
            'id_proof',
            'address_proof',
            'role',
            'password1',
            'password2'
        ]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        block = cleaned_data.get("block")
        flat_number = (cleaned_data.get("flat_number") or "").strip()

        if role == "resident":
            if not block:
                self.add_error("block", "Please select a block.")
            if not flat_number:
                self.add_error("flat_number", "Please enter your flat number.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        block = self.cleaned_data.get("block")
        flat_number = (self.cleaned_data.get("flat_number") or "").strip()

        if block and flat_number:
            user.flat, _ = Flat.objects.get_or_create(
                block=block.name,
                number=flat_number,
                defaults={"floor": 0},
            )

        if commit:
            user.save()

        return user


class FamilyMemberForm(forms.ModelForm):
    household_type = forms.ChoiceField(
        choices=User.HOUSEHOLD_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = FamilyMember
        fields = ["household_type", "name", "gender", "relationship", "date_of_birth"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "relationship": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }

    def __init__(self, *args, resident=None, **kwargs):
        self.resident = resident
        super().__init__(*args, **kwargs)
        if resident is not None:
            self.fields["household_type"].initial = resident.household_type

    def clean(self):
        cleaned_data = super().clean()
        household_type = cleaned_data.get("household_type")
        relationship = (cleaned_data.get("relationship") or "").strip()

        if household_type == "family" and not relationship:
            self.add_error("relationship", "Please enter the relationship.")
        elif household_type == "bachelor" and not relationship:
            cleaned_data["relationship"] = "Self"

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.resident is not None:
            self.resident.household_type = self.cleaned_data["household_type"]
            if commit:
                self.resident.save(update_fields=["household_type"])
            instance.resident = self.resident

        if commit:
            instance.save()

        return instance
