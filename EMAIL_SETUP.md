# Email Setup

The project now sends real email notifications through Django SMTP settings.
You can keep the values either in environment variables or in a project `.env` file.

## Gmail SMTP example

Use a Gmail address with a Google App Password.

```powershell
$env:EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
$env:EMAIL_HOST="smtp.gmail.com"
$env:EMAIL_PORT="587"
$env:EMAIL_HOST_USER="your_gmail@gmail.com"
$env:EMAIL_HOST_PASSWORD="your_16_char_app_password"
$env:EMAIL_USE_TLS="true"
$env:EMAIL_USE_SSL="false"
$env:DEFAULT_FROM_EMAIL="Apartment Management <your_gmail@gmail.com>"
$env:NOTIFICATION_ADMIN_EMAILS="admin1@example.com,admin2@example.com"
```

Then run:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

## `.env` file option

Create a file named `.env` in the project root and copy the values from `.env.example`.
Then restart the Django server.

## Test email

Before testing login, ticket, or payment notifications, send one direct test email:

```powershell
.\.venv\Scripts\python.exe manage.py send_test_email your_email@gmail.com
```

If SMTP is wrong, this command will print the exact error.

## Notes

- Login notifications go to the user who signed in.
- Ticket creation emails go to the resident and to staff/admin recipients.
- Payment creation emails go to the resident.
- Payment completion emails go to the resident and to staff/admin recipients.
- If `NOTIFICATION_ADMIN_EMAILS` is empty, the app also uses email addresses from existing `staff` and `admin` users in the database.
