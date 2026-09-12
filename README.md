# RFQ Follow-Up Reminder

![License](https://img.shields.io/badge/license-LGPL--3-blue)
![Odoo](https://img.shields.io/badge/Odoo-18.0-blueviolet)
![Languages](https://img.shields.io/badge/languages-9-orange)
![Version](https://img.shields.io/badge/version-18.0.1.1.0-informational)

Automatically chase vendors who never answered your Request for Quotation. A daily scheduled action emails the vendor an escalating sequence of reminders — gentle, firm, then final — while the RFQ stays unanswered. Configurable cadence, editable templates, no JavaScript.

## Why

Odoo 18 ships a vendor reminder mechanism, but it only chases the **receipt date** of already-confirmed purchase orders (`_send_reminder_mail` runs on `state == 'purchase'` with `acknowledged == False`). Nothing chases a vendor who has simply never replied to a Request for Quotation sitting in `state == 'sent'`. Buyers track those by hand. This module closes that gap with a daily cron and three editable `mail.template` records.

## Features

- **Three escalating emails** -- a gentle nudge, a firm reminder, then a final notice that copies the buyer in.
- **Configurable cadence** -- reminder offsets (default 3 / 7 / 14 days after the RFQ was sent) are set under **Purchase > Configuration > Settings**.
- **Editable templates** -- the three messages are `mail.template` records (`template_rfq_reminder_1` / `_2` / `_3`); admins edit subject, body, and sender under Settings > Technical > Email Templates.
- **One email per run** -- the cron always sends the most-escalated reminder that is due, so enabling the module on an instance full of old RFQs never dumps three emails at once.
- **De-duplication** -- each fired reminder is recorded in `x_rfq_reminder_sent` (a comma-separated Char), so a second cron pass never re-sends the same email.
- **Per-RFQ opt-out** -- the **Auto-Chase Vendor** toggle on the purchase order form lets buyers stop chasing a specific RFQ.
- **Sent-only filter** -- only RFQs in `state == 'sent'` are processed. Drafts and confirmed orders are skipped; resetting an RFQ to draft restarts the chase cycle.
- **Disable from the UI** -- the cron is a plain `ir.cron` record, toggled under Settings > Technical > Scheduled Actions.

## How It Works

1. The module inherits `purchase.order` and adds `x_rfq_sent_date`, `x_rfq_reminder_sent`, `x_rfq_reminder_count` and `x_rfq_reminder_enabled`, plus the classmethod `_cron_send_rfq_reminders()`.
2. When an RFQ transitions from `draft` to `sent`, `write()` stamps `x_rfq_sent_date`. Resetting it to `draft` clears the stamp and the reminder history.
3. A daily `ir.cron` record calls `_cron_send_rfq_reminders()` once a day.
4. The method searches RFQs in `state == 'sent'` with auto-chase enabled, computes the days elapsed since `x_rfq_sent_date`, and for each one sends the most-escalated reminder whose configured offset has been reached.
5. The matching `mail.template` is rendered against the order and sent with `force_send=True`; the fired token (`r1`, `r2`, `r3`) is appended to `x_rfq_reminder_sent`.

## Technical Details

| Field            | Value                                                  |
|------------------|--------------------------------------------------------|
| Module Version | 18.0.1.1.0                                             |
| Odoo Version     | 18.0 Community + Enterprise                            |
| License          | LGPL-3                                                 |
| Dependencies     | `purchase`                                             |
| Python Deps      | none                                                   |
| Field Prefix     | `x_`                                                   |
| Backend code     | two model patches (`purchase.order`, `res.config.settings`) |
| Frontend code    | two view inherits (purchase order form, purchase settings) |
| Database changes | four fields on `purchase.order`                        |
| Mail templates   | 3 (gentle / firm / final) -- editable                  |
| Languages        | EN, FR, ES, DE, NL, PT-BR, IT, ZH-CN, AR (gettext PO)  |

## Fields Added

| Field                    | Type     | Description                                                                              |
|--------------------------|----------|------------------------------------------------------------------------------------------|
| `x_rfq_sent_date`        | Datetime | When the RFQ was first sent; anchor for the reminder schedule. Read-only.                 |
| `x_rfq_reminder_sent`    | Char     | Comma-separated tokens marking which reminders have fired (e.g. `r1,r2`). Read-only.      |
| `x_rfq_reminder_count`   | Integer  | Number of reminders already sent (computed from `x_rfq_reminder_sent`).                   |
| `x_rfq_reminder_enabled` | Boolean  | Auto-Chase Vendor toggle; untick to stop chasing a specific RFQ. Defaults to enabled.     |

## Installation

1. Drop `no_rfq_follow_up/` into your Odoo addons path.
2. **Apps -> Update Apps List** -> search "RFQ Follow-Up Reminder" -> **Install**.
3. The cron is enabled automatically; the default cadence is 3 / 7 / 14 days.

## Configuration

1. **Purchase > Configuration > Settings** -> "RFQ Follow-Up Reminders" -> set the first / second / final reminder offsets (days after the RFQ is sent).
2. **Settings > Technical > Email Templates** -> "RFQ Follow-Up: Gentle / Firm / Final Reminder" -> edit the subject, body, or sender.
3. **Settings > Technical > Scheduled Actions** -> "Purchase: Send RFQ follow-up reminders" -> toggle active or change the interval.

## Docker Setup (Development)

```bash
docker-compose up -d
```

Odoo: http://localhost:13447

## Running Tests

```bash
docker exec rfqfollowup-odoo-19 odoo --stop-after-init --db_host=db --db_user=odoo --db_password=odoo -d test_db -i no_rfq_follow_up --test-enable --test-tags /no_rfq_follow_up
```

Eight Python `TransactionCase` tests cover first-reminder send, no-resend, draft skip, disabled skip, confirmed-PO skip, the firm reminder at the second offset, long-overdue catch-up, and the draft-reset clearing the chase history.

## Languages

Ships with translations for:

| Code     | Language                |
|----------|-------------------------|
| `en_US`  | English (source)        |
| `fr`     | French                  |
| `es`     | Spanish                 |
| `de`     | German                  |
| `nl`     | Dutch                   |
| `pt_BR`  | Portuguese (Brazil)     |
| `it`     | Italian                 |
| `zh_CN`  | Chinese (Simplified)    |
| `ar`     | Arabic                  |

Each user sees the emails and form labels in the language set in **Preferences -> Language**. Regional variants (e.g. `fr_BE`, `nl_BE`) inherit from the base language via Odoo's standard fallback.

## Compatibility

- Odoo 18.0 Community + Enterprise

## Author

**Naim OUDAYET** -- Tunisia. <https://www.oudayet.com>

## License

LGPL-3 -- <https://www.gnu.org/licenses/lgpl-3.0.html>
