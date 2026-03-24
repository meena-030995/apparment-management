import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .services import generate_chat_reply


@login_required
def chat_page(request):
    starter_prompts = [
        "How do I pay my maintenance dues?",
        "How can I raise a maintenance ticket?",
        "What should security record for visitors?",
        "How do notices work in this system?",
    ]
    return render(
        request,
        "assistant/chatbot.html",
        {
            "starter_prompts": starter_prompts,
            "chatbot_enabled": bool(settings.OPENAI_API_KEY),
        },
    )


@login_required
@require_POST
def chat_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []
    if not isinstance(history, list):
        history = []

    if not message:
        return JsonResponse({"error": "Please enter a message."}, status=400)

    try:
        reply = generate_chat_reply(request.user, message, history)
    except Exception:
        return JsonResponse(
            {
                "error": (
                    "The AI assistant is temporarily unavailable right now. "
                    "Please try again in a moment."
                )
            },
            status=502,
        )

    return JsonResponse({"reply": reply})
