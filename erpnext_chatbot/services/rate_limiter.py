"""
Rate Limiter Service

Implements sliding window rate limiting using Frappe Cache (Redis-backed).
"""

import time
import frappe
from frappe import _
from typing import Optional


class RateLimitExceeded(frappe.ValidationError):
    """Custom exception for rate limit violations."""
    http_status_code = 429


def check_rate_limit(
    user: Optional[str] = None,
    limit: int = 20,
    window: int = 60,
    action: str = "chatbot_query"
) -> bool:
    """
    Check if user has exceeded rate limit using sliding window algorithm.

    Args:
        user: Username to rate limit (defaults to current user)
        limit: Maximum requests per window (default 20)
        window: Time window in seconds (default 60)
        action: Action being rate limited (for cache key)

    Returns:
        True if within limit

    Raises:
        RateLimitExceeded: If limit exceeded
    """
    if user is None:
        user = frappe.session.user

    # Administrator is exempt from rate limiting
    if user == "Administrator":
        return True

    cache_key = f"rate_limit:{action}:{user}"
    cache = frappe.cache()

    current_time = time.time()

    # Get existing timestamps from cache
    timestamps = cache.get_value(cache_key) or []

    # Remove timestamps outside current window
    timestamps = [ts for ts in timestamps if current_time - ts < window]

    if len(timestamps) >= limit:
        # Calculate time until next request allowed
        oldest_timestamp = min(timestamps)
        retry_after = int(window - (current_time - oldest_timestamp))

        frappe.throw(
            _("Rate limit exceeded. Please try again in {0} seconds.").format(retry_after),
            RateLimitExceeded
        )

    # Add current timestamp
    timestamps.append(current_time)

    # Store with expiry
    cache.set_value(cache_key, timestamps, expires_in_sec=window)

    return True


def get_remaining_requests(
    user: Optional[str] = None,
    limit: int = 20,
    window: int = 60,
    action: str = "chatbot_query"
) -> dict:
    """
    Get remaining requests for user within current window.

    Args:
        user: Username to check
        limit: Maximum requests per window
        window: Time window in seconds
        action: Action being rate limited

    Returns:
        Dictionary with remaining requests and reset time
    """
    if user is None:
        user = frappe.session.user

    cache_key = f"rate_limit:{action}:{user}"
    cache = frappe.cache()

    current_time = time.time()

    # Get existing timestamps from cache
    timestamps = cache.get_value(cache_key) or []

    # Remove timestamps outside current window
    timestamps = [ts for ts in timestamps if current_time - ts < window]

    remaining = max(0, limit - len(timestamps))

    # Calculate reset time (when oldest request expires)
    if timestamps:
        oldest_timestamp = min(timestamps)
        reset_in = int(window - (current_time - oldest_timestamp))
    else:
        reset_in = 0

    return {
        "remaining": remaining,
        "limit": limit,
        "reset_in_seconds": reset_in,
        "window_seconds": window
    }


def reset_rate_limit(
    user: Optional[str] = None,
    action: str = "chatbot_query"
) -> bool:
    """
    Reset rate limit for a user (admin function).

    Args:
        user: Username to reset
        action: Action to reset

    Returns:
        True if reset successful
    """
    if user is None:
        user = frappe.session.user

    cache_key = f"rate_limit:{action}:{user}"
    cache = frappe.cache()
    cache.delete_value(cache_key)

    return True
