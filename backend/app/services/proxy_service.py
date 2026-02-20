"""IP Anonymization Proxy Service — masks scan origin IP.

Routes all outbound OSINT HTTP traffic through a configurable proxy
(SOCKS5/Tor, HTTP proxy, or rotating proxy list) to prevent the
application's real IP from being exposed to scanned vendors.

Supported modes:
- tor: SOCKS5 via local Tor proxy (default socks5://127.0.0.1:9050)
- socks5: Generic SOCKS5 proxy
- http: HTTP/HTTPS proxy
- rotating: Round-robin through a list of proxies
- none: No proxy (direct connection)

All OSINT tools and agents use get_scan_http_client() to obtain a
pre-configured httpx.AsyncClient with proxy, randomized User-Agent,
and audit logging.
"""

import logging
import random
import threading
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("cyberscore.proxy")

# Realistic browser User-Agents for fingerprint evasion
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

# Hosts that should NEVER be proxied (local services, LLM providers)
_PROXY_BYPASS_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "minio",
    "redis",
    "postgres",
    "keycloak",
    "qdrant",
}

# Thread-safe rotating proxy index
_rotating_index = 0
_rotating_lock = threading.Lock()


def _get_random_user_agent() -> str:
    """Return a random realistic browser User-Agent."""
    return random.choice(_USER_AGENTS)


def _parse_rotating_proxies() -> list[str]:
    """Parse comma-separated proxy list from config."""
    raw = settings.proxy_rotating_list
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _get_next_rotating_proxy() -> str | None:
    """Get next proxy from rotating list (round-robin)."""
    global _rotating_index
    proxies = _parse_rotating_proxies()
    if not proxies:
        return None
    with _rotating_lock:
        proxy = proxies[_rotating_index % len(proxies)]
        _rotating_index += 1
    return proxy


def get_proxy_url() -> str | None:
    """Resolve the current proxy URL based on configured mode.

    Returns:
        Proxy URL string or None if proxy is disabled.
    """
    mode = settings.proxy_mode.lower()

    if mode == "none" or not mode:
        return None

    if mode == "tor":
        return settings.proxy_tor_url or "socks5://127.0.0.1:9050"

    if mode == "socks5":
        return settings.proxy_socks5_url or None

    if mode == "http":
        return settings.proxy_http_url or None

    if mode == "rotating":
        return _get_next_rotating_proxy()

    logger.warning("Unknown proxy mode '%s', falling back to direct", mode)
    return None


def _should_bypass_proxy(url: str) -> bool:
    """Check if a URL should bypass the proxy (local services)."""
    try:
        parsed = httpx.URL(url)
        host = str(parsed.host).lower()
        # Bypass for local hosts and configured bypass patterns
        if host in _PROXY_BYPASS_HOSTS:
            return True
        # Bypass for private IP ranges
        if host.startswith("10.") or host.startswith("192.168.") or host.startswith("172."):
            return True
        # Bypass for custom patterns from config
        custom_bypass = settings.proxy_bypass_hosts
        if custom_bypass:
            for pattern in custom_bypass.split(","):
                if pattern.strip() and pattern.strip() in host:
                    return True
    except Exception:
        pass
    return False


def get_scan_http_client(
    timeout: float = 30.0,
    headers: dict[str, str] | None = None,
    follow_redirects: bool = True,
    **kwargs: Any,
) -> httpx.AsyncClient:
    """Create an httpx.AsyncClient configured with proxy and anonymization.

    This is the single entry point for all outbound OSINT HTTP traffic.
    Use this instead of raw ``httpx.AsyncClient()`` in tools and agents.

    Args:
        timeout: Request timeout in seconds.
        headers: Additional headers (merged with anonymization headers).
        follow_redirects: Whether to follow HTTP redirects.
        **kwargs: Extra kwargs passed to httpx.AsyncClient.

    Returns:
        Configured httpx.AsyncClient with proxy and randomized UA.
    """
    proxy_url = get_proxy_url()

    # Build anonymized headers
    anon_headers = {
        "User-Agent": _get_random_user_agent(),
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1",
    }
    if headers:
        anon_headers.update(headers)

    client_kwargs: dict[str, Any] = {
        "timeout": timeout,
        "follow_redirects": follow_redirects,
        "headers": anon_headers,
        **kwargs,
    }

    if proxy_url:
        client_kwargs["proxy"] = proxy_url
        logger.debug(
            "Creating proxied HTTP client (mode=%s, proxy=%s)",
            settings.proxy_mode,
            proxy_url[:30] + "..." if len(proxy_url) > 30 else proxy_url,
        )
    else:
        logger.debug("Creating direct HTTP client (proxy_mode=none)")

    return httpx.AsyncClient(**client_kwargs)


async def verify_proxy() -> dict[str, Any]:
    """Verify proxy connectivity and return the visible external IP.

    Makes a request to a public IP echo service through the proxy
    to confirm anonymization is working.

    Returns:
        Dict with proxy status, visible IP, and mode.
    """
    proxy_url = get_proxy_url()
    mode = settings.proxy_mode

    if mode == "none" or not proxy_url:
        return {
            "status": "disabled",
            "mode": mode,
            "proxy_url": None,
            "visible_ip": None,
            "message": "Proxy is disabled. Scans use direct connection.",
        }

    try:
        async with get_scan_http_client(timeout=15.0) as client:
            # Use multiple IP echo services for reliability
            for echo_url in [
                "https://api.ipify.org?format=json",
                "https://ifconfig.me/ip",
                "https://icanhazip.com",
            ]:
                try:
                    resp = await client.get(echo_url)
                    if resp.status_code == 200:
                        if "json" in echo_url:
                            ip = resp.json().get("ip", resp.text.strip())
                        else:
                            ip = resp.text.strip()
                        return {
                            "status": "active",
                            "mode": mode,
                            "proxy_url": proxy_url,
                            "visible_ip": ip,
                            "message": f"Proxy OK. Visible IP: {ip}",
                        }
                except Exception:
                    continue

        return {
            "status": "error",
            "mode": mode,
            "proxy_url": proxy_url,
            "visible_ip": None,
            "message": "Proxy configured but IP echo services unreachable.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "mode": mode,
            "proxy_url": proxy_url,
            "visible_ip": None,
            "message": f"Proxy connection failed: {exc}",
        }
