"""
Razorpay SDK client wrapper.

RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in .env.
This module is mocked in all tests — never hits Razorpay in CI.
"""

import razorpay

from app.config import settings


def get_client() -> razorpay.Client:
    """Return an authenticated Razorpay client instance."""
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
