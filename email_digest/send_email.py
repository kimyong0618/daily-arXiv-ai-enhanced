"""Send a multipart plain-text and HTML research digest over SMTP."""

from __future__ import annotations

import argparse
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def _recipients(value: str) -> list[str]:
    return [address.strip() for address in value.replace(";", ",").split(",") if address.strip()]


def build_message(
    username: str,
    recipients: list[str],
    subject: str,
    plain_text: str,
    html_text: str,
) -> MIMEMultipart:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = username
    message["To"] = ", ".join(recipients)
    message.attach(MIMEText(plain_text, "plain", "utf-8"))
    message.attach(MIMEText(html_text, "html", "utf-8"))
    return message


def send_digest(subject: str, plain_text: str, html_text: str) -> None:
    username = os.environ.get("MAIL_USERNAME", "").strip()
    password = os.environ.get("MAIL_PASSWORD", "").strip()
    recipients = _recipients(os.environ.get("MAIL_TO", ""))
    server = os.environ.get("MAIL_SMTP_SERVER", "smtp.qq.com").strip()
    try:
        port = int(os.environ.get("MAIL_SMTP_PORT", "465"))
    except ValueError as error:
        raise ValueError("MAIL_SMTP_PORT must be an integer") from error

    missing = [
        name
        for name, value in (
            ("MAIL_USERNAME", username),
            ("MAIL_PASSWORD", password),
            ("MAIL_TO", recipients),
            ("MAIL_SMTP_SERVER", server),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing mail configuration: {', '.join(missing)}")

    message = build_message(username, recipients, subject, plain_text, html_text)
    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(server, port, context=context, timeout=30) as smtp:
            smtp.login(username, password)
            smtp.sendmail(username, recipients, message.as_string())
    else:
        with smtplib.SMTP(server, port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(username, password)
            smtp.sendmail(username, recipients, message.as_string())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True, help="Generated HTML file")
    parser.add_argument("--plain", required=True, help="Generated plain-text file")
    parser.add_argument("--subject", required=True)
    args = parser.parse_args()
    send_digest(
        args.subject,
        Path(args.plain).read_text(encoding="utf-8"),
        Path(args.html).read_text(encoding="utf-8"),
    )
    print("Email digest sent successfully")


if __name__ == "__main__":
    main()
