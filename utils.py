import re
import datetime
from decimal import Decimal, InvalidOperation
from config import DATE_FMT, DATETIME_FMT, CURRENCY
from errors import ValidationError


def require_text(value, label):
    """Validate that value is non-empty after stripping whitespace."""
    if value is None:
        raise ValidationError(f"{label} is required.")
    cleaned = str(value).strip()
    if not cleaned:
        raise ValidationError(f"{label} cannot be empty.")
    return cleaned


def valid_contact(value, label="Contact number"):
    """Validate phone/contact: digits, optional leading +, spaces, dashes."""
    text = require_text(value, label)
    if not re.match(r"^\+?[\d\s\-]{7,20}$", text):
        raise ValidationError(f"{label} must contain only digits, spaces, and hyphens (7-20 chars).")
    return text


def valid_email(value, label="Email"):
    """Validate email: basic syntax check with @ and domain dot."""
    text = require_text(value, label)
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text):
        raise ValidationError(f"{label} format is invalid (e.g. user@example.com).")
    return text.lower()


def parse_money(text, label="Amount"):
    """Parse text into Decimal, rejecting negative values."""
    raw = require_text(text, label).replace(",", "").replace(CURRENCY, "")
    try:
        val = Decimal(raw)
    except InvalidOperation:
        raise ValidationError(f"{label} must be a valid number.")
    if val < Decimal("0.00"):
        raise ValidationError(f"{label} cannot be negative.")
    return val.quantize(Decimal("0.01"))


def parse_positive_int(text, label="Quantity"):
    """Parse text into an integer > 0."""
    raw = require_text(text, label)
    try:
        val = int(raw)
    except ValueError:
        raise ValidationError(f"{label} must be a valid whole number.")
    if val <= 0:
        raise ValidationError(f"{label} must be greater than zero.")
    return val


def parse_non_negative_int(text, label="Number"):
    """Parse text into an integer >= 0."""
    raw = require_text(text, label)
    try:
        val = int(raw)
    except ValueError:
        raise ValidationError(f"{label} must be a valid whole number.")
    if val < 0:
        raise ValidationError(f"{label} cannot be negative.")
    return val


def parse_date(text, label="Date"):
    """Parse YYYY-MM-DD string into date object."""
    raw = require_text(text, label)
    try:
        return datetime.datetime.strptime(raw, DATE_FMT).date()
    except ValueError:
        raise ValidationError(f"{label} must follow format YYYY-MM-DD.")


def now_str():
    """Return current timestamp in standardized DATETIME_FMT."""
    return datetime.datetime.now().strftime(DATETIME_FMT)


def money(value):
    """Format Decimal, float, or str as ₱#,##0.00."""
    if value is None:
        return f"{CURRENCY}0.00"
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except InvalidOperation:
            value = Decimal("0.00")
    return f"{CURRENCY}{value:,.2f}"
