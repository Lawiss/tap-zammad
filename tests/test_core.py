"""Tests standard tap features using the built-in SDK tests library."""

import datetime
import os

from singer_sdk.testing import get_standard_tap_tests, get_tap_test_class

from tap_zammad.tap import TapZammad

SAMPLE_CONFIG = {
    "start_date": os.environ["TAP_ZAMMAD_START_DATE"],
    "auth_token": os.environ["TAP_ZAMMAD_AUTH_TOKEN"],
    "api_base_url": os.environ["TAP_ZAMMAD_API_BASE_URL"],
}


# Run standard built-in tap tests from the SDK:
TestTapZammad = get_tap_test_class(tap_class=TapZammad, config=SAMPLE_CONFIG)


# TODO: Create additional tests as appropriate for your tap.
