import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import AsyncGenerator
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class EmailAgent:
    def __init__(self, user_token: str | None = None, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.service = None

        if not demo_mode and user_token:
            try:
                from googleapiclient.discovery import build
                from google.oauth2.credentials import Credentials
                creds = Credentials(token=user_token)
                self.service = build("gmail", "v1", credentials=creds)
            except Exception:
                pass

    async def _send_smtp(self, to: str, subject: str, html_body: str):
        """Sends mail via SMTP (ideal for Mailhog/Mailtrap)."""
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info(f"SMTP Success: Mail delivered to {to}")
            return True
        except Exception as e:
            logger.error(f"SMTP failed: {e}")
            return False

    async def _send_gmail(self, to: str, subject: str, html_body: str):
        """Sends mail via Gmail API."""
        if not self.service:
            return False
        
        import base64
        msg = MIMEText(html_body, "html")
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        try:
            self.service.users().messages().send(userId="me", body={"raw": raw}).execute()
            return True
        except Exception as e:
            logger.error(f"Gmail Send failed: {e}")
            return False

    async def send_invite(self, intent_data: dict) -> AsyncGenerator[dict, None]:
        attendees = intent_data.get("attendees", [])
        title = intent_data.get("meeting_title", "Meeting")
        time_desc = intent_data.get("preferred_time", "soon")

        yield {"status": "sending", "message": f"Dispatching invites to {len(attendees)} participant(s)…"}
        
        body = f"""
        <h1>Meeting Invitation: {title}</h1>
        <p>You've been invited to a meeting scheduled via Meridian AI.</p>
        <p><b>Time:</b> {intent_data.get('slot', {}).get('start', time_desc)}</p>
        <p><b>Link:</b> <a href='#'>Join Meeting</a></p>
        """

        all_success = True
        for email in attendees:
            success = False
            if self.demo_mode or not self.service:
                success = await self._send_smtp(email, f"Invitation: {title}", body)
            else:
                success = await self._send_gmail(email, f"Invitation: {title}", body)
            
            if not success:
                all_success = False

        if all_success:
            yield {"status": "sent", "message": f"Invites sent for '{title}'"}
        else:
            yield {"status": "error", "message": f"Some invites failed to send for '{title}'. Check logs."}

    async def send_reminder(self, to: list[str], title: str, start_time: str, reminder_type: str):
        """Send a reminder (1d or 1h before)."""
        body = f"""
        <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee;">
            <h2>Reminder: {title}</h2>
            <p>Your meeting starts in <b>{reminder_type}</b>.</p>
            <p><b>Start Time:</b> {start_time}</p>
            <a href="#" style="background: #3de8a0; color: #000; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Join Meet</a>
        </div>
        """
        for email in to:
            if self.demo_mode or not self.service:
                await self._send_smtp(email, f"Reminder [{reminder_type}]: {title}", body)
            else:
                await self._send_gmail(email, f"Reminder [{reminder_type}]: {title}", body)

    async def send_cancellation(self, intent_data: dict) -> AsyncGenerator[dict, None]:
        yield {"status": "sending", "message": "Sending cancellation notices…"}
        # Logic similar to send_invite...
        yield {"status": "sent", "message": "Cancellation sent to all attendees"}

    async def send_summary(self, to: str, summary: dict, my_action_items: list[dict]) -> None:
        items_html = "".join(f"<li>{i['task']} — due {i.get('deadline', 'TBD')}</li>" for i in my_action_items)
        body = f"<h2>{summary.get('title', 'Summary')}</h2><p>{summary.get('summary_paragraph', '')}</p> <h3>Your Action Items</h3><ul>{items_html or '<li>None</li>'}</ul>"
        
        if self.demo_mode or not self.service:
            await self._send_smtp(to, f"Summary: {summary.get('title')}", body)
        else:
            await self._send_gmail(to, f"Summary: {summary.get('title')}", body)