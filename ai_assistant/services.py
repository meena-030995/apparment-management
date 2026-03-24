from django.conf import settings
from django.utils import timezone

def _flat_label(user):
    if not getattr(user, "flat", None):
        return "Not assigned"

    block = getattr(user.flat, "block", None)
    block_name = getattr(block, "name", "").strip()
    if block_name:
        return f"Flat {user.flat.number}, Block {block_name}"
    return f"Flat {user.flat.number}"


def _build_system_prompt(user):
    now = timezone.localtime().strftime("%d %b %Y, %I:%M %p")
    role = (user.role or "resident").title()

    return (
        "You are the AMS Apartment AI Assistant for an apartment community management platform. "
        "Be concise, practical, and friendly. Focus on helping users with apartment workflows such as "
        "maintenance tickets, dues, payment records, notices, visitor logs, and account guidance. "
        "Do not claim to perform actions you cannot actually perform. If the user needs a real system "
        "change, clearly tell them which page or team to contact. Do not invent personal account data, "
        "payment status, notices, or ticket details. Use the available profile context only.\n\n"
        f"Current local time: {now}\n"
        f"User role: {role}\n"
        f"Resident/flat context: {_flat_label(user)}\n"
        f"Username: {user.username}\n"
        "If the user asks general questions, provide actionable apartment-management guidance."
    )


def _response_text(response):
    output_text = getattr(response, "output_text", "")
    if output_text:
        return output_text.strip()

    output = getattr(response, "output", []) or []
    fragments = []
    for item in output:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", "")
            if text:
                fragments.append(text)
    return "\n".join(fragment.strip() for fragment in fragments if fragment.strip()).strip()


def _local_fallback_reply(user, message):
    lower_message = message.lower()
    flat_text = _flat_label(user)

    if any(keyword in lower_message for keyword in ["notice", "announcement"]):
        return (
            "You can view community notices from the Notice Board page in the dashboard navigation. "
            "Residents can open Notices to read active announcements, expiry details, and attached files if available."
        )

    if any(keyword in lower_message for keyword in ["ticket", "complaint", "maintenance", "issue", "repair"]):
        return (
            "To raise a maintenance request, open Create Ticket from the dashboard or navbar, enter the issue title "
            "and description, then submit it. You can track progress later from My Tickets."
        )

    if any(keyword in lower_message for keyword in ["pay", "payment", "due", "maintenance fee", "bill"]):
        return (
            f"For {flat_text}, you can check pending dues from Maintenance Dues and view completed transactions in "
            "Payment History. If a due is available, open it and continue through the payment flow shown in the portal."
        )

    if any(keyword in lower_message for keyword in ["visitor", "guest", "entry", "gate", "security"]):
        return (
            "Visitor activity is handled from the Visitor Logs module. Security can add the visitor name, phone, "
            "flat, purpose, entry time, and vehicle registration number, then update the exit when the visitor leaves."
        )

    if any(keyword in lower_message for keyword in ["login", "register", "account", "password"]):
        return (
            "You can create a resident account from Register, then log in from the Login page once the account is approved. "
            "If you cannot access your account, ask the admin or association office to verify your approval status."
        )

    if any(keyword in lower_message for keyword in ["flat", "block", "resident"]):
        return (
            f"Your current profile context is {flat_text}. Admin creates block names, and residents register using their "
            "block plus desired flat number so the account can be linked correctly."
        )

    return (
        "I can help with apartment portal guidance such as dues, payments, maintenance tickets, notices, visitor logs, "
        "registration, and resident workflows. Try asking something like 'How do I raise a ticket?' or "
        "'How do notices work in this system?'"
    )


def generate_chat_reply(user, message, history=None):
    message = (message or "").strip()
    if not message:
        return _local_fallback_reply(user, "")

    if not settings.OPENAI_API_KEY:
        return _local_fallback_reply(user, message)

    try:
        from openai import OpenAI
    except ImportError:
        return _local_fallback_reply(user, message)

    history = history or []
    conversation = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": _build_system_prompt(user)}],
        }
    ]

    for item in history[-8:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        conversation.append(
            {
                "role": role,
                "content": [{"type": "input_text", "text": content}],
            }
        )

    conversation.append(
        {
            "role": "user",
            "content": [{"type": "input_text", "text": message}],
        }
    )

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.responses.create(
            model=settings.OPENAI_CHAT_MODEL,
            input=conversation,
        )
    except Exception:
        return _local_fallback_reply(user, message)

    reply = _response_text(response)
    if not reply:
        return _local_fallback_reply(user, message)
    return reply
