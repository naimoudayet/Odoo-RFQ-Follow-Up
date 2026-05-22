# Copyright 2026 Naim OUDAYET
# License LGPL-3
"""
Tests for RFQ Follow-Up Reminder.

Coverage:
  - After the first offset elapses, the cron sends reminder 1 and stamps 'r1'.
  - A second cron pass the same day does NOT re-send.
  - A draft RFQ is skipped (only 'sent' RFQs are chased).
  - An RFQ with auto-chase disabled is skipped.
  - A confirmed PO ('purchase' state) is skipped.
  - The firm reminder fires once the second offset is reached.
  - Catch-up: an RFQ already past the final offset gets the most-escalated
    reminder only (one email), with the earlier tokens consumed silently.
  - Resetting an RFQ to draft clears the sent date + reminder history.

The cron entry point (`_cron_send_rfq_reminders`) is called directly:
TransactionCase does not run scheduled actions, and we want to assert on
side effects, not on the scheduler. `send_mail(force_send=True)` drains the
mail.mail queue synchronously, so the rows exist when the cron returns.
"""
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRfqFollowUp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PurchaseOrder = cls.env["purchase.order"]
        cls.MailMail = cls.env["mail.mail"]

        cls.vendor = cls.env["res.partner"].create({
            "name": "RFQ Test Vendor",
            "email": "rfq.vendor@example.com",
        })
        # type='consu' keeps the product purchasable without pulling in
        # stock-only constraints.
        cls.product = cls.env["product.product"].create({
            "name": "RFQ Test Component",
            "type": "consu",
            "list_price": 50.0,
        })

    def _make_rfq(self, sent_days_ago=None, state="sent", enabled=True):
        """Create a purchase.order and move it into `state`.

        When `sent_days_ago` is given, x_rfq_sent_date is back-dated by
        that many days so the cron sees the desired elapsed window. The
        write() override stamps x_rfq_sent_date on the draft->sent
        transition; the explicit write afterwards overrides it with the
        back-dated anchor.
        """
        order = self.PurchaseOrder.create({
            "partner_id": self.vendor.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_qty": 1.0,
                "price_unit": 50.0,
                "name": "RFQ Test Component",
            })],
        })
        if state and state != "draft":
            order.write({"state": state})
        vals = {"x_rfq_reminder_enabled": enabled}
        if sent_days_ago is not None:
            vals["x_rfq_sent_date"] = (
                fields.Datetime.now() - timedelta(days=sent_days_ago)
            )
        order.write(vals)
        return order

    def _count_mail(self, subject_fragment):
        """Count mail.mail rows whose subject contains `subject_fragment`."""
        return self.MailMail.search_count([
            ("subject", "ilike", subject_fragment),
        ])

    def test_first_reminder_sent(self):
        """RFQ sent 3 days ago -> the gentle reminder fires and stamps r1."""
        order = self._make_rfq(sent_days_ago=3)
        before = self._count_mail("Following up")

        self.PurchaseOrder._cron_send_rfq_reminders()

        self.assertEqual(
            self._count_mail("Following up") - before, 1,
            "The first cron pass must send exactly one gentle reminder.",
        )
        self.assertIn(
            "r1", order.x_rfq_reminder_sent or "",
            "x_rfq_reminder_sent must record the 'r1' token.",
        )
        self.assertEqual(order.x_rfq_reminder_count, 1)

    def test_reminder_not_resent(self):
        """Running the cron twice the same day sends the reminder once."""
        self._make_rfq(sent_days_ago=3)
        before = self._count_mail("Following up")

        self.PurchaseOrder._cron_send_rfq_reminders()
        self.PurchaseOrder._cron_send_rfq_reminders()

        self.assertEqual(
            self._count_mail("Following up") - before, 1,
            "The second cron pass must NOT re-send the gentle reminder.",
        )

    def test_draft_rfq_skipped(self):
        """A draft RFQ is never chased, even if it looks overdue."""
        order = self._make_rfq(sent_days_ago=10, state="draft")
        before = self._count_mail("Following up")

        self.PurchaseOrder._cron_send_rfq_reminders()

        self.assertEqual(
            self._count_mail("Following up") - before, 0,
            "Draft RFQs must be skipped by the follow-up cron.",
        )
        self.assertFalse(order.x_rfq_reminder_sent)

    def test_disabled_rfq_skipped(self):
        """An RFQ with auto-chase unticked is skipped."""
        order = self._make_rfq(sent_days_ago=10, enabled=False)
        before = self._count_mail("Following up")

        self.PurchaseOrder._cron_send_rfq_reminders()

        self.assertEqual(
            self._count_mail("Following up") - before, 0,
            "RFQs with auto-chase disabled must be skipped.",
        )
        self.assertFalse(order.x_rfq_reminder_sent)

    def test_confirmed_po_skipped(self):
        """A confirmed purchase order is not an RFQ and must be skipped."""
        order = self._make_rfq(sent_days_ago=10, state="purchase")
        before = self._count_mail("Following up")

        self.PurchaseOrder._cron_send_rfq_reminders()

        self.assertEqual(
            self._count_mail("Following up") - before, 0,
            "Confirmed purchase orders must be skipped by the cron.",
        )
        self.assertFalse(order.x_rfq_reminder_sent)

    def test_firm_reminder_at_second_offset(self):
        """RFQ sent 7 days ago -> firm reminder fires, gentle one consumed."""
        order = self._make_rfq(sent_days_ago=7)
        before_firm = self._count_mail("still pending")
        before_gentle = self._count_mail("Following up")

        self.PurchaseOrder._cron_send_rfq_reminders()

        self.assertEqual(
            self._count_mail("still pending") - before_firm, 1,
            "At the second offset the firm reminder must be the one emailed.",
        )
        self.assertEqual(
            self._count_mail("Following up") - before_gentle, 0,
            "The gentle reminder must be consumed silently, not emailed.",
        )
        self.assertIn("r1", order.x_rfq_reminder_sent or "")
        self.assertIn("r2", order.x_rfq_reminder_sent or "")

    def test_catch_up_sends_final_only(self):
        """RFQ sent 20 days ago -> only the final reminder is emailed."""
        order = self._make_rfq(sent_days_ago=20)
        before_final = self._count_mail("Final reminder")
        before_gentle = self._count_mail("Following up")
        before_firm = self._count_mail("still pending")

        self.PurchaseOrder._cron_send_rfq_reminders()

        self.assertEqual(
            self._count_mail("Final reminder") - before_final, 1,
            "A long-overdue RFQ must get exactly one final reminder.",
        )
        self.assertEqual(
            self._count_mail("Following up") - before_gentle, 0,
            "No gentle reminder email on a long-overdue RFQ.",
        )
        self.assertEqual(
            self._count_mail("still pending") - before_firm, 0,
            "No firm reminder email on a long-overdue RFQ.",
        )
        self.assertEqual(
            order.x_rfq_reminder_count, 3,
            "All three tokens must be recorded (one emailed, two consumed).",
        )

    def test_reset_to_draft_clears_history(self):
        """Resetting a sent RFQ to draft clears the chase state."""
        order = self._make_rfq(sent_days_ago=3)
        self.PurchaseOrder._cron_send_rfq_reminders()
        self.assertTrue(order.x_rfq_sent_date)
        self.assertTrue(order.x_rfq_reminder_sent)

        order.write({"state": "draft"})

        self.assertFalse(
            order.x_rfq_sent_date,
            "Resetting to draft must clear x_rfq_sent_date.",
        )
        self.assertFalse(
            order.x_rfq_reminder_sent,
            "Resetting to draft must clear the reminder history.",
        )
