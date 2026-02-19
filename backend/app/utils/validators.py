"""Input validation utilities for domains, IPs, and emails."""

import ipaddress
import re


_DOMAIN_PATTERN = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$"
)

_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def is_valid_domain(domain: str) -> bool:
    """Validate a domain name format.

    Args:
        domain: The domain string to validate.

    Returns:
        True if the domain is syntactically valid.
    """
    if not domain or len(domain) > 253:
        return False
    return _DOMAIN_PATTERN.match(domain) is not None


def is_valid_ip(ip: str) -> bool:
    """Validate an IPv4 or IPv6 address.

    Args:
        ip: The IP address string to validate.

    Returns:
        True if the IP address is valid.
    """
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    return True


def is_valid_email(email: str) -> bool:
    """Validate an email address format.

    Args:
        email: The email string to validate.

    Returns:
        True if the email is syntactically valid.
    """
    if not email or len(email) > 320:
        return False
    return _EMAIL_PATTERN.match(email) is not None


def normalize_domain(domain: str) -> str:
    """Normalize a domain to lowercase without trailing dot.

    Args:
        domain: The domain to normalize.

    Returns:
        Normalized domain string.
    """
    return domain.lower().rstrip(".")
