# Changelog

All notable changes to **RFQ Follow-Up Reminder** are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [20.0.1.1.0] - 2026-09-30

### Changed
- Ported to Odoo 20 (official `odoo:20` image; full test suite passes). The
  three reminder offsets are read with Odoo 20's typed settings API; the call
  the module used on 19 no longer exists on 20.
- App Store listing: the screenshots were retaken on Odoo 20.

## [19.0.1.1.0]

### Changed

- Settings fields now carry the `x_` prefix (`x_rfq_reminder_offset_1/2/3`) per
  ODOO_GUIDELINES 6. The `ir.config_parameter` keys are unchanged, so an existing
  installation keeps its configured cadence.

## [19.0.1.0.0] - 2026-05-22

### Added
- Initial release for Odoo 19.0.
- Daily scheduled action (`_cron_send_rfq_reminders`) that chases vendors who
  have not answered a Request for Quotation still in the `sent` state.
- Three escalating, editable `mail.template` records: gentle, firm, and final
  (the final reminder copies the buyer in).
- Configurable reminder offsets in **Purchase > Configuration > Settings**
  (defaults: 3 / 7 / 14 days after the RFQ was sent).
- Per-RFQ **Auto-Chase Vendor** toggle on the purchase order form.
- `x_rfq_sent_date`, `x_rfq_reminder_sent` and `x_rfq_reminder_count` fields on
  `purchase.order`; the sent date is stamped on the draft -> sent transition
  and cleared again if the RFQ is reset to draft.
- Eight Python `TransactionCase` tests.
- Translations for 9 languages (EN, FR, ES, DE, NL, PT-BR, IT, ZH-CN, AR).
