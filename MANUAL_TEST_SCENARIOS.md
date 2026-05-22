# Manual Test Scenarios — RFQ Follow-Up Reminder

Dev stack: `docker-compose up -d`, then open <http://localhost:13447> and use database `rfq19`.
Developer mode must be on to edit the read-only `RFQ Sent On` field for back-dating.

## 1. Sent-date stamping
1. **Purchase > Orders > Requests for Quotation > New**.
2. Pick a vendor, add a product line, Save.
3. Click **Send by Email** and send the RFQ.
4. Reopen the RFQ: **RFQ Sent On** shows the current date/time and **Auto-Chase Vendor** is ticked.

## 2. First reminder fires
1. On a sent RFQ, back-date **RFQ Sent On** by at least the first offset (default 3 days).
2. **Settings > Technical > Scheduled Actions > "Purchase: Send RFQ follow-up reminders" > Run Manually**.
3. The vendor receives the gentle reminder; the RFQ chatter logs the email; **Reminders Sent** = 1.

## 3. Escalation
1. Back-date **RFQ Sent On** past the second offset (default 7 days), run the cron: the firm reminder is sent, **Reminders Sent** = 2.
2. Back-date past the final offset (default 14 days), run the cron: the final reminder is sent with the buyer in CC, **Reminders Sent** = 3.

## 4. No double-send
1. Run the cron twice in a row on the same RFQ.
2. At most one email is sent per run; no reminder step repeats.

## 5. Catch-up never spams
1. Create a sent RFQ and back-date **RFQ Sent On** by 20+ days, with no reminders sent yet.
2. Run the cron once: exactly one email (the final reminder) is sent; **Reminders Sent** = 3.

## 6. Opt-out
1. Untick **Auto-Chase Vendor** on a sent, overdue RFQ.
2. Run the cron: no reminder is sent for that RFQ.

## 7. Confirmation stops the chase
1. Confirm a sent RFQ so it becomes a Purchase Order.
2. Run the cron: no further reminders for that order.

## 8. Reset to draft restarts the cycle
1. On a sent RFQ that already has reminders, use **Reset to Draft**.
2. **RFQ Sent On** and the reminder history are cleared; re-sending starts a fresh cycle.

## 9. Configurable cadence
1. **Purchase > Configuration > Settings > "RFQ Follow-Up Reminders"**.
2. Change the first / second / final offsets and Save; the cron uses the new values on its next run.

## 10. Languages
1. Switch the user language (**Preferences > Language**) across the 9 supported languages.
2. Form labels and the reminder emails render in the selected language.
