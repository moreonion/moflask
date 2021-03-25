import smtplib

from flask import current_app
from flask_mail import Connection as _Connection
from flask_mail import Mail as _Mail
from flask_mail import Message
from flask_mail import _Mail as __Mail

"""
Wrappers around flask_mail to support a custom MAIL FROM and local_hostname.
"""


class Connection(_Connection):
    def configure_host(self):
        kwargs = dict(local_hostname=self.mail.local_hostname)
        if self.mail.use_ssl:
            host = smtplib.SMTP_SSL(self.mail.server, self.mail.port, **kwargs)
        else:
            host = smtplib.SMTP(self.mail.server, self.mail.port, **kwargs)

        host.set_debuglevel(int(self.mail.debug))

        if self.mail.use_tls:
            host.starttls()
        if self.mail.username and self.mail.password:
            host.login(self.mail.username, self.mail.password)

        return host


class MailState(__Mail):
    def send(self, msg):
        """ Set custom headers and call parent. """
        if self.reply_to:
            msg.reply_to = self.reply_to
        with self.connect() as connection:
            connection.send(msg, self.envelope_from)

    def connect(self):
        """Opens a connection to the mail host."""
        app = getattr(self, "app", None) or current_app
        try:
            return Connection(app.extensions["mail"])
        except KeyError:
            raise RuntimeError("The curent application was not configured with Flask-Mail")


class Mail(_Mail):
    def send_message(self, *args, **kwargs):
        return self.send(Message(*args, **kwargs))

    def init_mail(self, config, debug=False, testing=False):
        state = MailState(
            config.get("MAIL_SERVER", "127.0.0.1"),
            config.get("MAIL_USERNAME"),
            config.get("MAIL_PASSWORD"),
            config.get("MAIL_PORT", 25),
            config.get("MAIL_USE_TLS", False),
            config.get("MAIL_USE_SSL", False),
            config.get("MAIL_DEFAULT_SENDER"),
            int(config.get("MAIL_DEBUG", debug)),
            config.get("MAIL_MAX_EMAILS"),
            config.get("MAIL_SUPPRESS_SEND", testing),
            config.get("MAIL_ASCII_ATTACHMENTS", False),
        )
        state.envelope_from = config.get("MAIL_ENVELOPE_FROM", None)
        state.local_hostname = config.get("MAIL_LOCAL_HOSTNAME", None)
        state.reply_to = config.get("MAIL_REPLY_TO", None)
        return state
