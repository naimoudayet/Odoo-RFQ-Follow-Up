# Copyright 2026 Naim OUDAYET
# License LGPL-3
"""
Cron-driven escalating follow-up reminders for unanswered RFQs.

The gap this fills
------------------
Odoo 19's ``purchase.order`` already ships a reminder mechanism
(``_send_reminder_mail`` / ``_get_orders_to_remind``), but it only targets
*confirmed* orders (``state == 'purchase'`` with ``acknowledged == False``)
and chases the **receipt date**. Nothing chases a vendor who has simply
never answered a Request for Quotation still sitting in ``state == 'sent'``.
Buyers track those by hand in spreadsheets. This module adds a daily cron
that emails the vendor an escalating sequence of reminders.

Design notes
------------
* ``x_rfq_sent_date`` -- Odoo stores no "RFQ was emailed on" date
  (``date_order`` is the order *deadline*). We stamp our own the first
  time the order transitions into ``sent`` by hooking ``write()``; every
  send path (``message_post`` with ``mark_rfq_as_sent``,
  ``print_quotation``, a manual state change) ends in
  ``write({'state': 'sent'})``.
* Resetting an RFQ to ``draft`` clears the stamp + token history, so a
  re-sent RFQ starts a fresh chase cycle.
* ``x_rfq_reminder_sent`` -- a comma-separated Char of fired tokens
  (``r1,r2,r3``). A relational model would be overkill for three flags;
  the Char de-duplicates across cron runs and is trivial to assert on.
* The cron sends **at most one email per RFQ per run**, always the
  most-escalated step that is due -- enabling the module on an instance
  full of week-old RFQs never dumps three emails at once.
* Offsets (default 3 / 7 / 14 days) are read from ``ir.config_parameter``
  so admins tune the cadence from Purchase Settings without touching code.
"""
from odoo import api, fields, models

# Tokens recorded in x_rfq_reminder_sent. Module-level so the cron, the
# helpers and the tests all speak the same dialect.
TOKEN_1 = "r1"
TOKEN_2 = "r2"
TOKEN_3 = "r3"

# Fixed escalation order: r1 gentle -> r2 firm -> r3 final.
REMINDER_TOKENS = (TOKEN_1, TOKEN_2, TOKEN_3)

TEMPLATE_XMLIDS = {
    TOKEN_1: "no_rfq_follow_up.template_rfq_reminder_1",
    TOKEN_2: "no_rfq_follow_up.template_rfq_reminder_2",
    TOKEN_3: "no_rfq_follow_up.template_rfq_reminder_3",
}

# ir.config_parameter keys + their hard defaults (days after the RFQ was
# sent). The default is the fallback used before Purchase Settings is saved.
OFFSET_PARAMS = {
    TOKEN_1: ("no_rfq_follow_up.offset_1", 3),
    TOKEN_2: ("no_rfq_follow_up.offset_2", 7),
    TOKEN_3: ("no_rfq_follow_up.offset_3", 14),
}


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    x_rfq_sent_date = fields.Datetime(
        string="RFQ Sent On",
        copy=False,
        readonly=True,
        help="When this Request for Quotation was first sent to the vendor. "
             "Stamped automatically on the draft -> sent transition and used "
             "as the anchor for the follow-up reminder schedule.",
    )
    x_rfq_reminder_sent = fields.Char(
        string="RFQ Reminders Sent",
        default="",
        copy=False,
        readonly=True,
        help="Comma-separated tokens marking which follow-up reminders have "
             "already fired for this RFQ (e.g. 'r1,r2'). Used by the daily "
             "cron to avoid sending the same reminder twice.",
    )
    x_rfq_reminder_count = fields.Integer(
        string="Reminders Sent",
        compute="_compute_x_rfq_reminder_count",
        store=True,
        help="Number of follow-up reminder emails already sent to the vendor "
             "for this RFQ.",
    )
    x_rfq_reminder_enabled = fields.Boolean(
        string="Auto-Chase Vendor",
        default=True,
        copy=False,
        help="When enabled, the daily scheduled action emails the vendor an "
             "escalating follow-up reminder while this RFQ stays unanswered. "
             "Untick to stop chasing this particular RFQ.",
    )

    @api.depends("x_rfq_reminder_sent")
    def _compute_x_rfq_reminder_count(self):
        for order in self:
            sent = order.x_rfq_reminder_sent or ""
            order.x_rfq_reminder_count = len(
                [part for part in sent.split(",") if part.strip()]
            )

    # ------------------------------------------------------------------
    # Sent-date stamping
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        # Cover the rare path of an RFQ created straight into 'sent' state
        # (e.g. an import) without ever passing through write().
        to_stamp = orders.filtered(
            lambda o: o.state == "sent" and not o.x_rfq_sent_date
        )
        if to_stamp:
            to_stamp.write({"x_rfq_sent_date": fields.Datetime.now()})
        return orders

    def write(self, vals):
        res = super().write(vals)
        new_state = vals.get("state")
        if new_state == "sent":
            to_stamp = self.filtered(lambda o: not o.x_rfq_sent_date)
            if to_stamp:
                to_stamp.write({"x_rfq_sent_date": fields.Datetime.now()})
        elif new_state == "draft":
            # A reset RFQ should chase from scratch when it is re-sent.
            to_reset = self.filtered("x_rfq_sent_date")
            if to_reset:
                to_reset.write({
                    "x_rfq_sent_date": False,
                    "x_rfq_reminder_sent": "",
                })
        return res

    # ------------------------------------------------------------------
    # Reminder helpers
    # ------------------------------------------------------------------
    def _rfq_reminder_token_sent(self, token):
        """Return True if ``token`` is already recorded in x_rfq_reminder_sent."""
        self.ensure_one()
        sent = self.x_rfq_reminder_sent or ""
        return token in {
            part.strip() for part in sent.split(",") if part.strip()
        }

    def _mark_rfq_reminder_sent(self, token):
        """Append ``token`` to x_rfq_reminder_sent if not already present."""
        self.ensure_one()
        if self._rfq_reminder_token_sent(token):
            return
        existing = (self.x_rfq_reminder_sent or "").strip(",")
        new_value = f"{existing},{token}" if existing else token
        # sudo(): the cron runs as base.user_root, but the write must also
        # succeed when a buyer triggers a reminder on an RFQ they don't own.
        self.sudo().write({"x_rfq_reminder_sent": new_value})

    def _send_rfq_reminder(self, token):
        """Render + send the reminder template for ``token``, then stamp it.

        Returns the created mail.mail id, or False if the template lookup
        failed (defensive -- the templates load from data and should always
        exist post-install).
        """
        self.ensure_one()
        template = self.env.ref(
            TEMPLATE_XMLIDS[token], raise_if_not_found=False
        )
        if not template:
            return False
        # force_send=True: the mail.mail queue cron may not run before the
        # vendor checks their inbox, which would blunt the follow-up.
        mail_id = template.send_mail(self.id, force_send=True)
        self._mark_rfq_reminder_sent(token)
        return mail_id

    @api.model
    def _rfq_reminder_offsets(self):
        """Return ``[(token, days), ...]`` in fixed escalation order.

        Days come from ir.config_parameter (set via Purchase Settings); a
        missing or non-integer value falls back to the hard default.
        """
        get_param = self.env["ir.config_parameter"].sudo().get_param
        offsets = []
        for token in REMINDER_TOKENS:
            key, default = OFFSET_PARAMS[token]
            raw = get_param(key, default)
            try:
                days = int(raw)
            except (TypeError, ValueError):
                days = default
            offsets.append((token, max(days, 0)))
        return offsets

    @api.model
    def _cron_send_rfq_reminders(self):
        """Daily entry point -- chase every unanswered RFQ.

        For each RFQ still in ``sent`` state with auto-chase enabled, work
        out how many days have elapsed since it was sent and send the
        most-escalated reminder whose offset has been reached. Earlier
        steps that are also due (e.g. when the module is enabled on an
        instance full of old RFQs) are marked as consumed without an
        email, so the vendor never receives a burst of three messages.
        """
        today = fields.Date.context_today(self)
        offsets = self._rfq_reminder_offsets()

        orders = self.search([
            ("state", "=", "sent"),
            ("x_rfq_reminder_enabled", "=", True),
            ("x_rfq_sent_date", "!=", False),
        ])
        for order in orders:
            elapsed = (today - order.x_rfq_sent_date.date()).days
            due = [
                token for token, days in offsets
                if elapsed >= days
                and not order._rfq_reminder_token_sent(token)
            ]
            if not due:
                continue
            # `due` keeps escalation order: consume the earlier ones,
            # actually email only the most escalated step.
            for token in due[:-1]:
                order._mark_rfq_reminder_sent(token)
            order._send_rfq_reminder(due[-1])
