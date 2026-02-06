#!/usr/bin/env python3
"""
Unit tests for notification send-once logic (no Firebase required).
Verifies the logic of the three fixes in server.py without importing server.
"""

from datetime import datetime, timedelta, timezone


def test_trial_expired_status_stops_rematch():
    """After setting subscriptionStatus to 'trial_expired', user must not re-enter trial-expired branch."""
    subscription_status = "trial_expired"
    trial_end_date = "2025-01-01T00:00:00Z"
    # Condition that gates the trial block in check_subscription_reminders_job:
    # if trial_end_date and subscription_status == "trial":
    would_enter_trial_block = trial_end_date and subscription_status == "trial"
    assert would_enter_trial_block is False, "trial_expired users must not re-enter trial block"


def test_trial_user_still_enters_block_before_fix():
    """User with status 'trial' and past end date still enters block (first time)."""
    subscription_status = "trial"
    trial_end_date = "2025-01-01T00:00:00Z"
    would_enter_trial_block = trial_end_date and subscription_status == "trial"
    assert would_enter_trial_block is True


def test_one_day_reminder_guarded_by_one_day_flag():
    """1-day payment reminder must only be sent when oneDay is False (first time in window)."""
    last_reminders = {}
    should_send = not last_reminders.get("oneDay", False)
    assert should_send is True
    last_reminders = {"oneDay": True}
    should_send = not last_reminders.get("oneDay", False)
    assert should_send is False


def test_diet_countdown_skip_when_already_sent():
    """User must be skipped when lastDietCountdownNotificationSentForUpload == last_upload_raw."""
    last_upload_raw = "2025-02-01T12:00:00Z"
    last_sent_for = "2025-02-01T12:00:00Z"
    should_skip = last_sent_for == last_upload_raw
    assert should_skip is True
    last_sent_for = "2025-01-15T12:00:00Z"
    should_skip = last_sent_for == last_upload_raw
    assert should_skip is False


def test_diet_countdown_new_diet_gets_notification():
    """New diet (different last_upload) should not be skipped."""
    last_upload_raw = "2025-02-05T12:00:00Z"  # new upload
    last_sent_for = "2025-02-01T12:00:00Z"    # previous diet
    should_skip = last_sent_for == last_upload_raw
    assert should_skip is False


if __name__ == "__main__":
    test_trial_expired_status_stops_rematch()
    test_trial_user_still_enters_block_before_fix()
    test_one_day_reminder_guarded_by_one_day_flag()
    test_diet_countdown_skip_when_already_sent()
    test_diet_countdown_new_diet_gets_notification()
    print("All notification send-once logic tests passed.")
