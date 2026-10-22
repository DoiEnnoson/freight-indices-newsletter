#!/usr/bin/env python3
"""
Subscriber Manager
==================

Manages newsletter subscribers stored in a private Google Sheet that is fed
by the signup Google Form (columns: Timestamp, Email Address, Consent).

Daily run (double opt-in):
- New form entries get a confirmation email with a token in the subject
- Replies to that email confirm the subscription
- Emails with "Unsubscribe" in the subject unsubscribe the sender
- Unconfirmed entries are deleted after 30 days, unsubscribed after 3 years

Email addresses are never written to the logs, because Actions logs are public.
"""

import email
import imaplib
import json
import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from email.utils import parseaddr, parsedate_to_datetime

import gspread

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

SHEET_ID = "1ZOS8FMWxDX9EjS7R47MNV8YkdTp5SIIxY563-POBLao"
SIGNUP_PAGE_URL = "https://doiennoson.github.io/freight-indices-newsletter/"

# Columns written by the form
COL_EMAIL = "Email Address"
# Columns managed by this script (appended after the form columns)
MANAGED_COLUMNS = ["Status", "Token", "ConfirmationSentUTC", "ConfirmedUTC", "UnsubscribedUTC"]

STATUS_PENDING = "pending"
STATUS_CONFIRMED = "confirmed"
STATUS_UNSUBSCRIBED = "unsubscribed"
STATUS_DUPLICATE = "duplicate"

TOKEN_PREFIX = "FIN-"
UNSUBSCRIBE_SUBJECT = "Unsubscribe"
PENDING_MAX_AGE = timedelta(days=30)
UNSUBSCRIBED_MAX_AGE = timedelta(days=3 * 365)
MAILBOX_LOOKBACK_DAYS = 35
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_email_config():
    """Parse EMAIL_CONFIG environment variable."""
    config = os.getenv("EMAIL_CONFIG")
    if not config:
        raise ValueError("EMAIL_CONFIG environment variable not set")

    parts = config.split(":")
    if len(parts) != 4:
        raise ValueError("EMAIL_CONFIG must be in format: email:password:smtp_server:port")

    return {
        "email": parts[0],
        "password": parts[1],
        "smtp_server": parts[2],
        "smtp_port": int(parts[3])
    }


def now_utc():
    return datetime.now(timezone.utc)


def format_time(dt):
    return dt.strftime(TIME_FORMAT)


def parse_time(value):
    if not value:
        return None
    return datetime.strptime(value, TIME_FORMAT).replace(tzinfo=timezone.utc)


def normalize_email(address):
    return (address or "").strip().lower()


def open_worksheet():
    """Open the subscriber worksheet with the service account from GOOGLE_SERVICE_ACCOUNT."""
    info = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    if not info:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT environment variable not set")

    gc = gspread.service_account_from_dict(json.loads(info))
    return gc.open_by_key(SHEET_ID).sheet1


def load_rows(ws):
    """Load all rows as dicts and make sure the managed columns exist."""
    values = ws.get_all_values()
    if not values:
        raise ValueError("Subscriber sheet is empty, expected form header row")

    header = values[0]
    if COL_EMAIL not in header:
        raise ValueError(f"Subscriber sheet has no '{COL_EMAIL}' column")

    missing = [c for c in MANAGED_COLUMNS if c not in header]
    if missing:
        header = header + missing
        ws.update(range_name=gspread.utils.rowcol_to_a1(1, 1), values=[header])
        logger.info(f"➕ Added managed columns: {', '.join(missing)}")

    rows = []
    for values_row in values[1:]:
        values_row = values_row + [""] * (len(header) - len(values_row))
        rows.append(dict(zip(header, values_row)))

    return header, rows


def save_managed_columns(ws, header, rows):
    """Write back only the managed columns, so form columns are never touched."""
    if not rows:
        return

    first_col = header.index(MANAGED_COLUMNS[0]) + 1
    start = gspread.utils.rowcol_to_a1(2, first_col)
    end = gspread.utils.rowcol_to_a1(len(rows) + 1, first_col + len(MANAGED_COLUMNS) - 1)
    ws.update(range_name=f"{start}:{end}", values=[[row[c] for c in MANAGED_COLUMNS] for row in rows])


def get_confirmed_emails():
    """Return the unique confirmed subscriber addresses."""
    ws = open_worksheet()
    _, rows = load_rows(ws)

    emails = []
    for row in rows:
        address = normalize_email(row[COL_EMAIL])
        if row["Status"] == STATUS_CONFIRMED and address and address not in emails:
            emails.append(address)

    logger.info(f"✅ Loaded {len(emails)} confirmed subscriber(s)")
    return emails


def send_confirmation_email(server, config, address, token):
    """Send the double opt-in confirmation email."""
    msg = MIMEText(
        "Hallo,\n\n"
        "jemand hat diese Adresse für den wöchentlichen Freight Indices Newsletter angemeldet.\n\n"
        "Um die Anmeldung zu bestätigen, antworte einfach auf diese E-Mail. "
        "Der Inhalt deiner Antwort spielt keine Rolle, nur der Betreff muss erhalten bleiben.\n\n"
        "Wenn du dich nicht angemeldet hast, ignoriere diese E-Mail. "
        "Du erhältst dann keine weiteren Nachrichten, und deine Adresse wird nach 30 Tagen gelöscht.\n\n"
        f"Datenschutzhinweis: {SIGNUP_PAGE_URL}privacy.html\n",
        "plain",
        "utf-8"
    )
    msg["Subject"] = f"Bitte Anmeldung bestätigen: Freight Indices Newsletter [{TOKEN_PREFIX}{token}]"
    msg["From"] = config["email"]
    msg["To"] = address
    server.send_message(msg)


def fetch_mailbox_messages(config):
    """Return (subject, sender, date) of recent confirmation replies and unsubscribe requests."""
    mail = imaplib.IMAP4_SSL(config['smtp_server'].replace('smtp', 'imap'), 993, timeout=30)
    mail.login(config['email'], config['password'])

    messages = []
    try:
        result, _ = mail.select('inbox', readonly=True)
        if result != 'OK':
            raise Exception(f"IMAP select failed: {result}")

        since_date = (datetime.now() - timedelta(days=MAILBOX_LOOKBACK_DAYS)).strftime("%d-%b-%Y")
        ids = set()
        for keyword in (TOKEN_PREFIX, UNSUBSCRIBE_SUBJECT):
            result, data = mail.search(None, f'SINCE {since_date} SUBJECT "{keyword}"')
            if result != 'OK':
                raise Exception(f"IMAP search failed: {result}")
            ids.update(data[0].split())

        for msg_id in ids:
            result, data = mail.fetch(msg_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
            if result != 'OK':
                continue

            msg = email.message_from_bytes(data[0][1])
            subject = str(make_header(decode_header(msg.get('Subject', ''))))
            sender = normalize_email(parseaddr(msg.get('From', ''))[1])
            try:
                date = parsedate_to_datetime(msg.get('Date')).astimezone(timezone.utc)
            except (TypeError, ValueError):
                date = now_utc()
            messages.append((subject, sender, date))
    finally:
        mail.logout()

    logger.info(f"📧 Found {len(messages)} candidate message(s) in mailbox")
    return messages


def apply_mailbox_messages(rows, messages, own_address):
    """Confirm rows by token and unsubscribe rows by sender address."""
    by_token = {row["Token"]: row for row in rows if row["Token"]}
    confirmed = unsubscribed = 0

    for subject, sender, date in messages:
        if sender == own_address:
            continue

        for token, row in by_token.items():
            if f"{TOKEN_PREFIX}{token}" in subject and row["Status"] == STATUS_PENDING:
                row["Status"] = STATUS_CONFIRMED
                row["ConfirmedUTC"] = format_time(date)
                confirmed += 1

        if UNSUBSCRIBE_SUBJECT.lower() in subject.lower():
            for row in rows:
                sent = parse_time(row["ConfirmationSentUTC"])
                if (normalize_email(row[COL_EMAIL]) == sender
                        and row["Status"] in (STATUS_PENDING, STATUS_CONFIRMED)
                        and sent is not None and sent < date):
                    row["Status"] = STATUS_UNSUBSCRIBED
                    row["UnsubscribedUTC"] = format_time(date)
                    unsubscribed += 1

    logger.info(f"✅ Confirmed: {confirmed}, unsubscribed: {unsubscribed}")


def process_new_rows(rows, server, config):
    """Send confirmation emails to new form entries."""
    active = {
        normalize_email(row[COL_EMAIL])
        for row in rows
        if row["Status"] in (STATUS_PENDING, STATUS_CONFIRMED)
    }
    sent = duplicates = 0

    for row in rows:
        address = normalize_email(row[COL_EMAIL])
        if row["Status"] or not address:
            continue

        if address in active:
            row["Status"] = STATUS_DUPLICATE
            duplicates += 1
            continue

        token = secrets.token_hex(4)
        try:
            send_confirmation_email(server, config, address, token)
        except smtplib.SMTPRecipientsRefused:
            logger.warning("⚠️ Confirmation email refused for one address, will retry next run")
            continue
        row["Status"] = STATUS_PENDING
        row["Token"] = token
        row["ConfirmationSentUTC"] = format_time(now_utc())
        active.add(address)
        sent += 1

    logger.info(f"📤 Confirmation emails sent: {sent}, duplicates skipped: {duplicates}")


def rows_to_delete(rows):
    """Return sheet row numbers of expired entries, bottom first."""
    now = now_utc()
    expired = []

    for i, row in enumerate(rows):
        sent = parse_time(row["ConfirmationSentUTC"])
        unsub = parse_time(row["UnsubscribedUTC"])
        if row["Status"] == STATUS_PENDING and sent and now - sent > PENDING_MAX_AGE:
            expired.append(i + 2)
        elif row["Status"] == STATUS_UNSUBSCRIBED and unsub and now - unsub > UNSUBSCRIBED_MAX_AGE:
            expired.append(i + 2)
        elif row["Status"] == STATUS_DUPLICATE:
            expired.append(i + 2)

    return sorted(expired, reverse=True)


def run_subscriber_manager():
    """Process signups, confirmations and unsubscribes."""
    logger.info("=" * 80)
    logger.info("👥 Subscriber Manager")
    logger.info("=" * 80)

    config = parse_email_config()
    ws = open_worksheet()
    header, rows = load_rows(ws)
    logger.info(f"📋 Loaded {len(rows)} row(s) from subscriber sheet")

    try:
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['email'], config['password'])
            process_new_rows(rows, server, config)

        messages = fetch_mailbox_messages(config)
        apply_mailbox_messages(rows, messages, normalize_email(config['email']))
    finally:
        # Persist tokens of confirmation emails already sent, even if a later step failed
        save_managed_columns(ws, header, rows)

    for row_number in rows_to_delete(rows):
        ws.delete_rows(row_number)

    counts = {}
    for row in rows:
        counts[row["Status"] or "new"] = counts.get(row["Status"] or "new", 0) + 1
    logger.info(f"📊 Status counts: {counts}")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        run_subscriber_manager()
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        exit(1)
