# Register your models here.
from django.contrib import admin
from .models import ActivityLog, FamilyMember, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "flat", "is_approved")
    list_filter = ("role", "is_approved", "flat__block")
    search_fields = ("username", "email", "phone", "flat__number", "flat__block")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("user__username", "description")


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "resident", "relationship", "gender", "age")
    list_filter = ("gender", "resident__household_type")
    search_fields = ("name", "resident__username", "resident__flat__number")
