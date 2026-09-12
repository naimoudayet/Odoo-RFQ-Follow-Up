# RFQ Follow-Up Reminder

![License](https://img.shields.io/badge/license-LGPL--3-blue)
![Odoo](https://img.shields.io/badge/Odoo-18.0%20%7C%2019.0-blueviolet)
![Languages](https://img.shields.io/badge/languages-9-orange)

**Author: Naim OUDAYET**

Automatically chase vendors who never answered your Request for Quotation. A daily scheduled action emails the vendor an escalating sequence of reminders — gentle, firm, then final — while the RFQ stays unanswered. Configurable cadence, editable templates, no JavaScript.

## Where the code lives

| Branch       | Purpose                                                              |
|--------------|----------------------------------------------------------------------|
| `19.0`       | **App Store branch, Odoo 19.** Addon-only, drops into `addons_path`.  |
| `19.0-dev`   | Development branch with Dockerfile, demo stack, manual-test scenarios.|
| `18.0`       | **App Store branch, Odoo 18.** Same module, backported.               |
| `18.0-dev`   | Development branch for the Odoo 18 series.                            |
| `main`       | This landing page only.                                               |

## Install

Get it from the **Odoo App Store**, or check out the branch matching your Odoo
version and copy `no_rfq_follow_up/` into your `addons_path`. Full documentation
lives on that branch's README.

## License

LGPL-3 — <https://www.gnu.org/licenses/lgpl-3.0.html>

(c) **Naim OUDAYET** — <https://www.oudayet.com>
