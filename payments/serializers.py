from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        payment = Payment(**validated_data)
        request = self.context.get("request")
        payment._notification_source = (
            "api" if request and "/api/" in request.path else "system"
        )
        payment.save()
        return payment

    class Meta:
        model = Payment
        fields = "__all__"
