from rest_framework import serializers

from core.notifications import send_registration_notification
from flats.models import Block, Flat

from .models import User


class UserSerializer(serializers.ModelSerializer):
    flat_label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "role",
            "id_proof",
            "address_proof",
            "flat",
            "flat_label",
            "is_approved",
        ]

    def get_flat_label(self, obj):
        return str(obj.flat) if obj.flat else None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    block = serializers.PrimaryKeyRelatedField(
        queryset=Block.objects.all(),
        required=False,
        allow_null=True,
    )
    flat_number = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "role",
            "block",
            "flat_number",
            "id_proof",
            "address_proof",
            "password",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs.get("role") == "resident":
            if not attrs.get("block"):
                raise serializers.ValidationError({"block": "Please select a block."})
            if not (attrs.get("flat_number") or "").strip():
                raise serializers.ValidationError(
                    {"flat_number": "Please enter your flat number."}
                )
        return attrs

    def create(self, validated_data):
        role = validated_data["role"]
        raw_password = validated_data["password"]
        block = validated_data.pop("block", None)
        flat_number = (validated_data.pop("flat_number", "") or "").strip()
        flat = None

        if block and flat_number:
            flat, _ = Flat.objects.get_or_create(
                block=block.name,
                number=flat_number,
                defaults={"floor": 0},
            )

        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            phone=validated_data["phone"],
            role=role,
            flat=flat,
            id_proof=validated_data.get("id_proof"),
            address_proof=validated_data.get("address_proof"),
            is_approved=role != "resident",
        )
        user.set_password(raw_password)
        user.save()
        send_registration_notification(user, raw_password, created_at=user.date_joined)
        return user
