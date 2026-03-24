# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.activity_logs import log_activity
from .forms import NoticeForm
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .serializers import NoticeSerializer


@login_required
def create_notice(request):

    if request.user.role not in ["staff", "admin"]:
        return redirect("dashboard")

    if request.method == "POST":

        form = NoticeForm(request.POST, request.FILES)

        if form.is_valid():

            notice = form.save(commit=False)

            notice.created_by = request.user

            notice.save()
            log_activity(
                request.user,
                "notice_created",
                f"Created notice '{notice.title}'.",
                {"notice_id": notice.id},
            )
            messages.success(request, "Notice published successfully.")

            return redirect("notice_list")

        messages.error(request, "Please correct the errors below.")

    else:
        form = NoticeForm()

    return render(
        request,
        "notices/create_notice.html",
        {"form": form}
    )
    
    # View Notice Board
from .models import Notice

@login_required
def notice_list(request):

    notices = Notice.objects.all().order_by("-created_at")

    return render(
        request,
        "notices/notice_list.html",
        {"notices": notices}
    )


class NoticeListAPI(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notice.objects.all().order_by("-created_at")
    serializer_class = NoticeSerializer


class NoticeCreateAPI(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NoticeSerializer

    def get_queryset(self):
        return Notice.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role not in ["staff", "admin"]:
            raise PermissionDenied("Only staff or admin can create notices.")
        notice = serializer.save(created_by=self.request.user)
        log_activity(
            self.request.user,
            "notice_created",
            f"Created notice '{notice.title}' via API.",
            {"notice_id": notice.id},
        )
    
