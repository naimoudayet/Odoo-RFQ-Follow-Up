# Copyright 2026 Naim OUDAYET
# License LGPL-3
{
    "name": "RFQ Follow-Up Reminder",
    "summary": "Cron-driven escalating email reminders that chase vendors who "
               "have not answered a sent Request for Quotation.",
    "description": "RFQ Follow-Up Reminder runs a daily scheduled action that "
                   "scans every Request for Quotation still in the sent state "
                   "and emails the vendor an escalating sequence of follow-up "
                   "reminders: a gentle nudge, a firm reminder, then a final "
                   "notice. Reminder offsets default to 3, 7 and 14 days after "
                   "the RFQ was sent and are configurable from Purchase "
                   "Settings. Each reminder is tracked per order so the cron "
                   "never sends the same email twice, and a per-RFQ toggle "
                   "lets buyers stop chasing a specific vendor. The three "
                   "messages are editable mail.template records. Native Odoo "
                   "only chases the receipt date of confirmed purchase orders "
                   "and has no mechanism to chase an unanswered RFQ. Pure "
                   "server-side logic plus view inherits. No new models, no "
                   "JavaScript.",
    "version": "19.0.1.1.0",
    "category": "Purchases",
    "website": "https://www.oudayet.com",
    "author": "Naim OUDAYET",
    "maintainers": ["naimoudayet"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "depends": ["purchase"],
    "data": [
        "data/mail_template_data.xml",
        "data/ir_cron.xml",
        "views/purchase_order_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [
        "demo/demo_screenshot_data.xml",
    ],
    "images": [
        "static/description/banner.png",
    ],
    "price": 0,
    "currency": "USD",
    "support": "contact@oudayet.com",
}
