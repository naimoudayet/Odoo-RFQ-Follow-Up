# Copyright 2026 Naim OUDAYET
# License LGPL-3
"""
Purchase Settings entries for the RFQ follow-up reminder cadence.

The three offsets are persisted as ``ir.config_parameter`` rows via the
``config_parameter`` attribute. ``purchase_order._rfq_reminder_offsets``
reads the same keys with the same hard defaults, so the cron works
correctly even before an admin ever opens and saves the settings page.
"""
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    rfq_reminder_offset_1 = fields.Integer(
        string="First Reminder (days after sent)",
        default=3,
        config_parameter="no_rfq_follow_up.offset_1",
        help="Days after an RFQ is sent before the first (gentle) follow-up "
             "email is sent to the vendor.",
    )
    rfq_reminder_offset_2 = fields.Integer(
        string="Second Reminder (days after sent)",
        default=7,
        config_parameter="no_rfq_follow_up.offset_2",
        help="Days after an RFQ is sent before the second (firm) follow-up "
             "email is sent. Should be larger than the first reminder.",
    )
    rfq_reminder_offset_3 = fields.Integer(
        string="Final Reminder (days after sent)",
        default=14,
        config_parameter="no_rfq_follow_up.offset_3",
        help="Days after an RFQ is sent before the final follow-up email is "
             "sent, with the buyer copied in. Should be larger than the "
             "second reminder.",
    )
