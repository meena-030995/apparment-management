import logging
from html import escape

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone


logger = logging.getLogger(__name__)


def _send_email(subject, message, recipients, html_message=None):
    cleaned_recipients = sorted({email for email in recipients if email})
    if not cleaned_recipients:
        return

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=cleaned_recipients,
        )
        if html_message:
            email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
    except Exception:
        logger.exception("Email notification failed for subject '%s'.", subject)


def _staff_and_admin_emails():
    configured = list(getattr(settings, "NOTIFICATION_ADMIN_EMAILS", []))
    User = get_user_model()
    role_emails = list(
        User.objects.filter(role__in=["staff", "admin"], email__isnull=False)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    return sorted(set(configured + role_emails))


def _company_name():
    return getattr(settings, "COMPANY_NAME", "Apartment Management")


def _apartment_name():
    return getattr(settings, "APARTMENT_NAME", "AMS")


def _format_timestamp(value):
    if not value:
        return "Not available"
    return timezone.localtime(value).strftime("%d %b %Y, %I:%M %p")


def _format_currency(value):
    return f"Rs. {value}"


def _resident_flat_details(user):
    flat = getattr(user, "flat", None)
    if flat is None:
        return "Not assigned", "Not assigned"
    return getattr(flat, "number", "Not assigned"), getattr(flat, "block", "Not assigned")


def _render_html_email(title, greeting, intro, sections, closing_lines):
    section_html = []
    for heading, rows in sections:
        if not rows:
            continue
        row_html = "".join(
            (
                "<tr>"
                f"<td style='padding:10px 0;color:#6b7280;font-size:14px;font-weight:600;"
                f"width:42%;vertical-align:top'>{escape(str(label))}</td>"
                f"<td style='padding:10px 0;color:#111827;font-size:14px'>{escape(str(value))}</td>"
                "</tr>"
            )
            for label, value in rows
        )
        section_html.append(
            "<div style='margin:24px 0 0'>"
            f"<div style='font-size:15px;font-weight:700;color:#4c1d95;margin-bottom:10px'>{escape(heading)}</div>"
            "<table style='width:100%;border-collapse:collapse'>"
            f"{row_html}"
            "</table>"
            "</div>"
        )

    closing_html = "".join(
        f"<p style='margin:0 0 12px;color:#4b5563;font-size:15px;line-height:1.7'>{escape(line)}</p>"
        for line in closing_lines
    )

    return (
        "<!doctype html>"
        "<html><body style='margin:0;padding:0;background:#f4f1fb;font-family:Segoe UI,Arial,sans-serif'>"
        "<div style='max-width:680px;margin:0 auto;padding:32px 16px'>"
        "<div style='background:linear-gradient(135deg,#4c1d95,#7c3aed);padding:28px 32px;"
        "border-radius:24px 24px 0 0;color:#fff'>"
        f"<div style='font-size:28px;font-weight:800;letter-spacing:-0.03em'>{escape(title)}</div>"
        f"<div style='margin-top:8px;font-size:15px;opacity:0.9'>{escape(_apartment_name())}</div>"
        "</div>"
        "<div style='background:#fff;border-radius:0 0 24px 24px;padding:32px;"
        "box-shadow:0 18px 50px rgba(76,29,149,0.12)'>"
        f"<p style='margin:0 0 16px;color:#111827;font-size:16px;line-height:1.7'>{escape(greeting)}</p>"
        f"<p style='margin:0;color:#4b5563;font-size:15px;line-height:1.7'>{escape(intro)}</p>"
        f"{''.join(section_html)}"
        "<div style='margin-top:24px'>"
        f"{closing_html}"
        "</div>"
        "</div></div></body></html>"
    )


def _render_login_alert_html(user, login_time):
    return (
        "<!doctype html>"
        "<html><body style='margin:0;padding:0;background:#161411;font-family:Segoe UI,Arial,sans-serif'>"
        "<div style='max-width:680px;margin:0 auto;padding:28px 16px'>"
        "<div style='background:#1d1a16;border:1px solid rgba(212,190,154,0.2);border-radius:28px;"
        "overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,0.28)'>"
        "<div style='padding:34px 34px 30px;background:linear-gradient(135deg,#12354a,#009688);color:#fff'>"
        f"<div style='font-size:14px;letter-spacing:0.28em;text-transform:uppercase;opacity:0.75'>{escape(_apartment_name())} Apartment</div>"
        "<div style='margin-top:14px;font-size:54px;line-height:1.02;font-weight:800;letter-spacing:-0.05em'>Login Alert</div>"
        "<div style='margin-top:18px;font-size:18px;line-height:1.6;max-width:360px;opacity:0.96'>"
        "A sign-in was detected on your account."
        "</div>"
        "</div>"
        "<div style='padding:34px'>"
        f"<p style='margin:0 0 16px;color:#f6f1e8;font-size:16px;line-height:1.7'>Hello {escape(user.username)},</p>"
        f"<p style='margin:0;color:#f6f1e8;font-size:16px;line-height:1.8'>We detected a login to your {_apartment_name()} Apartment account.</p>"
        "<div style='margin-top:28px;border:1px solid rgba(255,255,255,0.09);border-radius:22px;overflow:hidden;"
        "background:rgba(255,255,255,0.02)'>"
        "<div style='padding:18px 24px;border-bottom:1px solid rgba(255,255,255,0.06);color:#ffffff;font-size:17px;font-weight:700'>"
        "Login Details"
        "</div>"
        "<div style='padding:22px 24px'>"
        f"<div style='margin:0 0 14px;color:#f6f1e8;font-size:15px;line-height:1.7'><strong>Date &amp; Time:</strong> {escape(login_time)}</div>"
        f"<div style='margin:0;color:#f6f1e8;font-size:15px;line-height:1.7'><strong>Role:</strong> {escape(user.get_role_display())}</div>"
        "</div>"
        "</div>"
        "<p style='margin:28px 0 0;color:#f6f1e8;font-size:16px;line-height:1.8'>If this was you, no action is required.</p>"
        "<p style='margin:16px 0 0;color:#d7cfbf;font-size:15px;line-height:1.8'>"
        "If this wasn't you, please reset your password or contact the association office immediately."
        "</p>"
        f"<p style='margin:28px 0 0;color:#d7cfbf;font-size:15px;line-height:1.8'>Warm regards,<br>{escape(_apartment_name())} Management</p>"
        "</div></div></div></body></html>"
    )


def send_registration_notification(user, temporary_password, created_at=None):
    flat_number, block_name = _resident_flat_details(user)
    created_on = _format_timestamp(created_at or timezone.now())

    subject = "Registration / Account Created"
    message = (
        f"Dear {user.username},\n\n"
        f"Welcome to {_apartment_name()}! Your resident account has been successfully created.\n\n"
        f"Account Created On: {created_on}\n\n"
        "Flat Details:\n\n"
        f"Flat No: {flat_number}\n\n"
        f"Block/Unit: {block_name}\n\n"
        "You can now log in to the resident portal to:\n\n"
        "Raise maintenance requests\n\n"
        "Pay maintenance and utility bills\n\n"
        "View notices and announcements\n\n"
        "Stay connected with the community\n\n"
        "Login Details:\n\n"
        f"Username: {user.email or user.phone or user.username}\n\n"
        f"Temporary Password: {temporary_password}\n\n"
        "For security reasons, we recommend changing your password after your first login.\n\n"
        "If you need any assistance getting started, feel free to contact the association office.\n\n"
        "We're glad to have you as part of our community :)\n\n"
        f"Warm regards,\n{_apartment_name()} Management"
    )
    html_message = _render_html_email(
        "Account Created",
        f"Dear {user.username},",
        f"Welcome to {_apartment_name()}! Your resident account has been successfully created.",
        [
            ("Account Details", [("Created On", created_on)]),
            ("Flat Details", [("Flat No", flat_number), ("Block/Unit", block_name)]),
            (
                "Login Details",
                [
                    ("Username", user.email or user.phone or user.username),
                    ("Temporary Password", temporary_password),
                ],
            ),
        ],
        [
            "You can now raise maintenance requests, pay dues, view notices, and stay connected with the community.",
            "For security reasons, we recommend changing your password after your first login.",
            "If you need any assistance getting started, feel free to contact the association office.",
            f"Warm regards, {_apartment_name()} Management",
        ],
    )
    _send_email(subject, message, [user.email], html_message=html_message)


def send_login_notification(user, request=None):
    flat_number, block_name = _resident_flat_details(user)
    login_time = _format_timestamp(timezone.now())

    subject = "Login Notification"
    message = (
        f"Dear {user.username},\n\n"
        "We noticed a recent login to your resident portal for:\n\n"
        "Flat Details:\n\n"
        f"Flat No: {flat_number}\n\n"
        f"Block/Unit: {block_name}\n\n"
        f"Date & Time: {login_time}\n\n"
        f"Role: {user.get_role_display()}\n\n"
        "Hope you're enjoying the convenience of managing your apartment services online.\n\n"
        "If this wasn't you, please reset your password or contact the association office for assistance.\n\n"
        f"Warm regards,\n{_apartment_name()} Management"
    )
    html_message = _render_login_alert_html(user, login_time)
    _send_email(subject, message, [user.email], html_message=html_message)


def send_ticket_created_notifications(ticket):
    flat_number, block_name = _resident_flat_details(ticket.resident)

    resident_subject = "Ticket Raised Confirmation"
    resident_message = (
        f"Dear {ticket.resident.username},\n\n"
        "Your maintenance request has been successfully registered.\n\n"
        "Flat Details:\n\n"
        f"Flat No: {flat_number}\n\n"
        f"Block/Unit: {block_name}\n\n"
        "Request Details:\n\n"
        f"Ticket ID: {ticket.id}\n\n"
        f"Issue: {ticket.title}\n\n"
        f"Submitted On: {_format_timestamp(ticket.created_at)}\n\n"
        "Our maintenance team will look into this and resolve it as soon as possible.\n\n"
        "You can reply to this email for updates or additional information.\n\n"
        f"Warm regards,\n{_apartment_name()} Maintenance Team"
    )
    resident_html = _render_html_email(
        "Maintenance Request Registered",
        f"Dear {ticket.resident.username},",
        "Your maintenance request has been successfully registered.",
        [
            ("Flat Details", [("Flat No", flat_number), ("Block/Unit", block_name)]),
            (
                "Request Details",
                [
                    ("Ticket ID", ticket.id),
                    ("Issue", ticket.title),
                    ("Submitted On", _format_timestamp(ticket.created_at)),
                ],
            ),
        ],
        [
            "Our maintenance team will look into this and resolve it as soon as possible.",
            "You can reply to this email for updates or additional information.",
            f"Warm regards, {_apartment_name()} Maintenance Team",
        ],
    )
    _send_email(
        resident_subject,
        resident_message,
        [ticket.resident.email],
        html_message=resident_html,
    )

    staff_subject = f"New support ticket: #{ticket.id} {ticket.title}"
    staff_message = (
        "A new apartment ticket has been raised.\n\n"
        f"Ticket ID: {ticket.id}\n"
        f"Resident: {ticket.resident.username}\n"
        f"Resident email: {ticket.resident.email}\n"
        f"Category: {ticket.get_category_display()}\n"
        f"Status: {ticket.get_status_display()}\n"
        f"Title: {ticket.title}\n"
        f"Description: {ticket.description}\n"
    )
    staff_html = _render_html_email(
        "New Support Ticket",
        "Dear Team,",
        "A new apartment ticket has been raised.",
        [
            (
                "Ticket Details",
                [
                    ("Ticket ID", ticket.id),
                    ("Resident", ticket.resident.username),
                    ("Resident Email", ticket.resident.email),
                    ("Category", ticket.get_category_display()),
                    ("Status", ticket.get_status_display()),
                    ("Title", ticket.title),
                    ("Description", ticket.description),
                ],
            )
        ],
        [f"Warm regards, {_apartment_name()} System"],
    )
    _send_email(
        staff_subject,
        staff_message,
        _staff_and_admin_emails(),
        html_message=staff_html,
    )


def send_payment_created_notifications(payment, source="system"):
    flat_number, block_name = _resident_flat_details(payment.resident)
    resident_subject = "New Due Created via API" if source == "api" else "New Due Created"
    reference_id = payment.transaction_id or f"DUE-{payment.id}"
    due_date = (
        f"{payment.month} {payment.year}"
        if payment.month and payment.year
        else "Not available"
    )
    description = getattr(payment, "_payment_description", None) or "Maintenance Charges"

    resident_message = (
        f"Dear {payment.resident.username},\n\n"
        "A new due has been generated and added to your account.\n\n"
        "Flat Details:\n\n"
        f"Flat No: {flat_number}\n\n"
        f"Block/Unit: {block_name}\n\n"
        "Due Details:\n\n"
        f"Amount Due: {_format_currency(payment.amount)}\n\n"
        f"Due Date: {due_date}\n\n"
        f"Description: {description}\n\n"
        f"Reference: {reference_id}\n\n"
        "This has been automatically updated in the system.\n\n"
        "Kindly make the payment before the due date to avoid late charges.\n\n"
        "For any clarifications, feel free to contact the association office.\n\n"
        f"Warm regards,\n{_apartment_name()} Accounts Team"
    )
    resident_html = _render_html_email(
        "New Due Created",
        f"Dear {payment.resident.username},",
        "A new due has been generated and added to your account.",
        [
            ("Flat Details", [("Flat No", flat_number), ("Block/Unit", block_name)]),
            (
                "Due Details",
                [
                    ("Amount Due", _format_currency(payment.amount)),
                    ("Due Date", due_date),
                    ("Description", description),
                    ("Reference", reference_id),
                ],
            ),
        ],
        [
            "This has been automatically updated in the system.",
            "Kindly make the payment before the due date to avoid late charges.",
            "For any clarifications, feel free to contact the association office.",
            f"Warm regards, {_apartment_name()} Accounts Team",
        ],
    )
    _send_email(
        resident_subject,
        resident_message,
        [payment.resident.email],
        html_message=resident_html,
    )


def send_payment_paid_notifications(payment):
    flat_number, block_name = _resident_flat_details(payment.resident)
    resident_subject = "Payment Success Details"
    payment_method = getattr(payment, "_payment_method", None) or "Online"
    payment_type = getattr(payment, "_payment_type", None) or "Maintenance"
    payment_time = _format_timestamp(timezone.now())

    resident_message = (
        f"Dear {payment.resident.username},\n\n"
        "We have successfully received your payment.\n\n"
        "Flat Details:\n\n"
        f"Flat No: {flat_number}\n\n"
        f"Block/Unit: {block_name}\n\n"
        "Payment Details:\n\n"
        f"Amount Paid: {_format_currency(payment.amount)}\n\n"
        f"Payment Type: {payment_type}\n\n"
        f"Payment Method: {payment_method}\n\n"
        f"Transaction ID: {payment.transaction_id or 'Not provided'}\n\n"
        f"Date & Time: {payment_time}\n\n"
        "Your account has been updated accordingly.\n\n"
        "Thank you for your prompt payment.\n\n"
        f"Warm regards,\n{_apartment_name()} Accounts Team"
    )
    resident_html = _render_html_email(
        "Payment Received",
        f"Dear {payment.resident.username},",
        "We have successfully received your payment.",
        [
            ("Flat Details", [("Flat No", flat_number), ("Block/Unit", block_name)]),
            (
                "Payment Details",
                [
                    ("Amount Paid", _format_currency(payment.amount)),
                    ("Payment Type", payment_type),
                    ("Payment Method", payment_method),
                    ("Transaction ID", payment.transaction_id or "Not provided"),
                    ("Date & Time", payment_time),
                ],
            ),
        ],
        [
            "Your account has been updated accordingly.",
            "Thank you for your prompt payment.",
            f"Warm regards, {_apartment_name()} Accounts Team",
        ],
    )
    _send_email(
        resident_subject,
        resident_message,
        [payment.resident.email],
        html_message=resident_html,
    )

    admin_subject = f"Resident payment completed: {payment.resident.username}"
    admin_message = (
        "A resident payment has been completed.\n\n"
        f"Resident: {payment.resident.username}\n"
        f"Resident email: {payment.resident.email}\n"
        f"Month: {payment.month}\n"
        f"Year: {payment.year}\n"
        f"Amount: {payment.amount}\n"
        f"Transaction ID: {payment.transaction_id or 'Not provided'}\n"
    )
    admin_html = _render_html_email(
        "Resident Payment Completed",
        "Dear Team,",
        "A resident payment has been completed.",
        [
            (
                "Payment Details",
                [
                    ("Resident", payment.resident.username),
                    ("Resident Email", payment.resident.email),
                    ("Month", payment.month),
                    ("Year", payment.year),
                    ("Amount", payment.amount),
                    ("Transaction ID", payment.transaction_id or "Not provided"),
                ],
            )
        ],
        [f"Warm regards, {_apartment_name()} Accounts Team"],
    )
    _send_email(
        admin_subject,
        admin_message,
        _staff_and_admin_emails(),
        html_message=admin_html,
    )
