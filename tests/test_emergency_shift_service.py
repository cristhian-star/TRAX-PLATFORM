"""Pure tests: no application factory, database, dispatch or scheduler."""

import unittest
from unittest.mock import Mock
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import date, datetime, timedelta, timezone

from app.services.emergency_shift_service import (
    GUARDIA_DIURNA, GUARDIA_NOCTURNA, ShiftValidationError, plan_shift, plan_shifts,
)


class EmergencyShiftServiceTest(unittest.TestCase):
    # Explicit fixed-offset fixture, not a substitute for the deployment IANA gate.
    zone = timezone(timedelta(hours=-3))
    day = date(2026, 10, 5)
    start = datetime(2026, 10, 5, 22, tzinfo=timezone.utc)

    def plan(self, now, **kwargs):
        return plan_shift(self.day, GUARDIA_NOCTURNA, accepted=True,
                          clock=lambda: now, local_zone=self.zone, **kwargs)

    def test_reminder_boundaries(self):
        cases = [(timedelta(hours=7), 2, False),
                 (timedelta(hours=6, microseconds=1), 2, False),
                 (timedelta(hours=6), 1, False),
                 (timedelta(hours=3), 1, False),
                 (timedelta(hours=1, microseconds=1), 1, False),
                 (timedelta(hours=1), 0, True),
                 (timedelta(minutes=10), 0, True),
                 (timedelta(minutes=2), 0, True)]
        for delta, count, late in cases:
            with self.subTest(delta=delta):
                p = self.plan(self.start - delta)
                self.assertEqual(len(p.reminders), count)
                self.assertEqual(len(p.omitted_reminders), 2 - count)
                self.assertEqual(p.late, late)
                self.assertTrue(all(at > p.booked_at for _, at in p.reminders))

    def test_after_cutoff_rejected_without_rounding(self):
        for now in [self.start - timedelta(minutes=2) + timedelta(microseconds=1),
                    self.start - timedelta(seconds=119), self.start,
                    self.start + timedelta(hours=1)]:
            with self.subTest(now=now), self.assertRaises(ValueError):
                self.plan(now)

    def test_night_rolls_to_next_day_utc(self):
        p = self.plan(self.start - timedelta(days=1))
        self.assertEqual(p.starts_at, self.start)
        self.assertEqual(p.ends_at, self.start + timedelta(hours=12))
        self.assertIn("06/10/2026 a las 07:00 (día siguiente)", p.confirmation)
        self.assertEqual(p.accepted_at, p.booked_at)

    def test_day_and_consecutive_weekly_blocks(self):
        blocks = [(self.day, GUARDIA_DIURNA), (self.day, GUARDIA_NOCTURNA),
                  (self.day + timedelta(days=1), GUARDIA_DIURNA)]
        plans = plan_shifts(blocks, accepted=True,
                            clock=lambda: self.start - timedelta(days=1),
                            local_zone=self.zone)
        self.assertEqual(plans[0].starts_at.hour, 10)
        self.assertEqual(plans[0].ends_at, plans[1].starts_at)
        self.assertEqual(plans[1].ends_at, plans[2].starts_at)

    def test_duplicates_and_empty_batch_rejected(self):
        for blocks in [[], [(self.day, GUARDIA_DIURNA)] * 2]:
            with self.subTest(blocks=blocks), self.assertRaises(ValueError):
                plan_shifts(blocks, accepted=True, local_zone=self.zone)

    def test_acceptance_must_be_explicit_boolean(self):
        for accepted in [False, None, 1, "true"]:
            with self.subTest(accepted=accepted), self.assertRaises(ValueError):
                plan_shift(self.day, GUARDIA_DIURNA, accepted=accepted)

    def test_invalid_kind_date_and_naive_clock(self):
        for day, kind in [(self.day, "OTHER"), ("2026-10-05", GUARDIA_DIURNA)]:
            with self.subTest(day=day, kind=kind), self.assertRaises(ValueError):
                plan_shift(day, kind, accepted=True)
        with self.assertRaises(ValueError):
            self.plan(datetime(2026, 10, 1))

    def test_month_year_transition(self):
        p = plan_shift(date(2026, 12, 31), GUARDIA_NOCTURNA, accepted=True,
                       clock=lambda: self.start, local_zone=self.zone)
        self.assertEqual(p.ends_at.date(), date(2027, 1, 1))

    def test_equivalent_instants_and_determinism(self):
        now = self.start - timedelta(hours=7)
        self.assertEqual(self.plan(now), self.plan(now.astimezone(self.zone)))

    def test_day_cutoff_microseconds(self):
        for hour, minute, second, microsecond, valid in [
            (6, 57, 59, 999999, True), (6, 58, 0, 0, True),
            (6, 58, 0, 1, False), (6, 59, 59, 999999, False),
            (7, 0, 0, 0, False),
        ]:
            now = datetime(2026, 10, 5, hour, minute, second, microsecond, self.zone)
            with self.subTest(now=now):
                def invoke():
                    return plan_shift(self.day, GUARDIA_DIURNA, accepted=True,
                                      clock=lambda: now, local_zone=self.zone)
                if valid:
                    self.assertEqual(invoke().booked_at, now.astimezone(timezone.utc))
                else:
                    with self.assertRaises(ShiftValidationError):
                        invoke()

    def test_invalid_structure_matrix_before_clock(self):
        valid = (self.day, GUARDIA_DIURNA)
        cases = [None, [], (), "blocks", {}, 42, [None], [(self.day,)],
                 [(self.day, GUARDIA_DIURNA, "extra")], ["ab"],
                 [(self.day, None)], [(self.day, [])], [(self.day, {})],
                 [("2026-10-05", GUARDIA_DIURNA)],
                 [(datetime(2026, 10, 5), GUARDIA_DIURNA)],
                 [valid, None], [valid, (self.day, [])],
                 [valid, list(valid)], [(date.max, GUARDIA_NOCTURNA)]]
        for blocks in cases:
            with self.subTest(blocks=blocks):
                clock = Mock(side_effect=AssertionError("Clock must not run"))
                with self.assertRaises(ShiftValidationError) as error:
                    plan_shifts(blocks, accepted=True, clock=clock, local_zone=self.zone)
                self.assertIs(type(error.exception), ShiftValidationError)
                clock.assert_not_called()

    def test_list_tuple_normalization(self):
        kwargs = dict(accepted=True, clock=lambda: self.start - timedelta(days=1),
                      local_zone=self.zone)
        self.assertEqual(plan_shifts([[self.day, GUARDIA_DIURNA]], **kwargs),
                         plan_shifts(((self.day, GUARDIA_DIURNA),), **kwargs))

    def test_single_invalid_kind_is_public_error(self):
        for kind in [None, [], {}, 1, "UNKNOWN"]:
            with self.subTest(kind=kind), self.assertRaises(ShiftValidationError):
                plan_shift(self.day, kind, accepted=True)

    def test_end_of_month(self):
        p = plan_shift(date(2026, 10, 31), GUARDIA_NOCTURNA, accepted=True,
                       clock=lambda: self.start, local_zone=self.zone)
        self.assertEqual(p.ends_at.date(), date(2026, 11, 1))

    def test_real_iana_buenos_aires(self):
        try:
            zone = ZoneInfo("America/Argentina/Buenos_Aires")
        except ZoneInfoNotFoundError as error:
            self.skipTest(f"IANA unavailable: {error}")
        p = plan_shift(self.day, GUARDIA_NOCTURNA, accepted=True,
                       clock=lambda: self.start - timedelta(hours=7))
        self.assertEqual(p.starts_at.astimezone(zone).hour, 19)
        self.assertEqual(p.starts_at, self.start)
        self.assertEqual(p.ends_at.astimezone(zone).date(), date(2026, 10, 6))
        self.assertEqual(p.ends_at.astimezone(zone).hour, 7)


if __name__ == "__main__":
    unittest.main()
