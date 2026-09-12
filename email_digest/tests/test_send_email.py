import os
import unittest
from unittest.mock import MagicMock, patch

from email_digest.send_email import build_message, send_digest


class SendEmailTests(unittest.TestCase):
    def test_message_has_plain_and_html_alternatives(self):
        message = build_message(
            "sender@example.com",
            ["reader@example.com"],
            "Digest",
            "plain",
            "<strong>html</strong>",
        )
        self.assertEqual(["text/plain", "text/html"], [part.get_content_type() for part in message.get_payload()])

    @patch.dict(
        os.environ,
        {
            "MAIL_USERNAME": "sender@example.com",
            "MAIL_PASSWORD": "app-password",
            "MAIL_TO": "one@example.com,two@example.com",
            "MAIL_SMTP_SERVER": "smtp.example.com",
            "MAIL_SMTP_PORT": "465",
        },
        clear=False,
    )
    @patch("email_digest.send_email.smtplib.SMTP_SSL")
    def test_ssl_sender_logs_in_and_sends_to_all_recipients(self, smtp_ssl):
        smtp = MagicMock()
        smtp_ssl.return_value.__enter__.return_value = smtp
        send_digest("Digest", "plain", "<p>html</p>")
        smtp.login.assert_called_once_with("sender@example.com", "app-password")
        self.assertEqual(
            ["one@example.com", "two@example.com"],
            smtp.sendmail.call_args.args[1],
        )


if __name__ == "__main__":
    unittest.main()
