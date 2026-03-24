from django.contrib import admin
from .models import Block, Flat


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Flat)
class FlatAdmin(admin.ModelAdmin):
    list_display = ("block", "number", "floor")
    list_filter = ("block", "floor")
    search_fields = ("block", "number")
