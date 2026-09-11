---
title: Temperature Excursion Response SOP
doc_id: QCL-QA-SOP-17
owner: Revathi Iyer
department: QA and Compliance
status: in_force
effective_date: 2026-04-01
revision: 4.2
applies_to:
  - Pune HQ
  - Nagpur DC
  - Guwahati DC
  - Coimbatore DC
---

# Temperature Excursion Response SOP

## 1. Purpose

1.1. This procedure defines the response to any suspected or confirmed temperature
excursion in Quillfern Cold Logistics Pvt. Ltd. warehouses, docks, cross-dock
lanes, owned reefer trucks and hired trucks working under Quillfern dispatch.
The procedure applies to vaccines, insulin, chilled dairy, paneer, frozen food,
and any customer stock moved under a written temperature commitment.

1.2. The purpose is to protect patient safety, food safety, customer evidence,
and the company record. A fast release is never preferred over a complete
temperature history. Staff must treat a missing record as a quality event until
QA closes it.

1.3. "Excursion" means a recorded temperature outside the allowed range for
longer than the allowed duration. A single hand-held thermometer reading is not
enough to release product after a breach; it may be used only to start immediate
containment while the logger history is retrieved.

## 2. Products and limits

2.1. Vaccines must remain between +2.0 C and +8.0 C. A vaccine high excursion is
declared when any approved sensor records more than +8.0 C for 15 continuous
minutes. A vaccine low excursion is declared when the record is below +2.0 C
for 10 continuous minutes.

2.2. Insulin must remain between +2.0 C and +8.0 C. An insulin high excursion is
declared when the approved record is more than +8.0 C for 20 continuous
minutes. An insulin low excursion is declared when the record is below +2.0 C
for 10 continuous minutes.

2.3. Milk and paneer must remain from 0.0 C to +4.0 C while in cold rooms and
reefer bodies. A dairy high excursion is declared when milk or paneer is above
+5.0 C for 30 continuous minutes, including staging time after dock release.

2.4. Frozen food must remain at or below -18.0 C. A frozen-food excursion is
declared when the approved record is warmer than -15.0 C for 20 continuous
minutes.

2.5. The Nagpur central hub is also referred to as "NGP hub" in older records.
For this SOP, Nagpur DC and NGP hub mean the same facility unless a customer
contract names a different annex.

2.6. Legacy staging note retained from revision 2.0: milk crates may remain on a
covered dock until +7.0 C for 45 minutes before QA notice is required. This
paragraph has not been relied on since revision 4.0 and is retained only because
customer annex QF-Dairy-11 still quotes it.

## 3. Approved records

3.1. For trips and rooms after 18 August 2025, Tessaline Telematics is the first
electronic source for approved temperature history. The API export named
"exception_csv_v2" is the preferred file.

3.2. For trips and rooms before 18 August 2025, Kalpa Fleet Systems remains an
accepted historical source. No staff member shall create a new Kalpa trip after
that date.

3.3. Independent USB loggers, customer loggers, and calibrated hand-held
thermometers may support an investigation, but they do not overrule the approved
electronic source unless QA documents a sensor failure.

3.4. Hand-written dock readings are acceptable only for the first containment
decision. They must be replaced by a downloaded electronic record before stock
is released, destroyed, returned, or billed.

## 4. Immediate containment

4.1. Stop movement of the affected pallet, tote, crate, reefer body, or room bay.
Do not load additional customer stock into the affected compartment.

4.2. Attach a red sleeve to the stock or truck file. The red sleeve contains the
customer intimation form, red hold tags, seal tape, and one spare calibrated
logger. If there is no physical sleeve, print form QCL-F-09 and write RED
SLEEVE MISSING at the top.

4.3. Move warehouse stock to quarantine bay Q-3 at Nagpur, Q-G2 at Guwahati, or
Q-C1 at Coimbatore. Truck stock must remain sealed unless QA instructs unloading
for product safety.

4.4. Photograph the sensor display, seal number, dock clock, and pallet labels.
The first four photographs must be uploaded before anyone debates stock
disposition. Do not wait for the manager to arrive.

4.5. Do not warm, chill, re-ice, ventilate, or hide the probe in order to make a
display look normal. Corrective measures may protect product, but the record
must continue to show the product environment honestly.

4.6. If a reefer unit is unstable on the road, the driver shall stop at a lit
fuel plaza or toll rest area, call Fleet Control, and keep the engine running
unless there is a fire, police order, or personal safety threat.

## 5. Notifications

5.1. Pharma critical stock means vaccines, insulin, and any medicine named by a
customer as patient critical. The customer must be notified within 2 hours of a
confirmed pharma critical excursion.

5.2. Dairy customers must be notified by the next scheduled customer service
check-in unless spoilage is visible, odour is present, or the temperature is
above +8.0 C. In those cases customer service must notify within 4 hours.

5.3. Frozen-food restaurant chains must receive an exception notice by the end of
the business day when the excursion is confirmed. If the vehicle is still on the
road, Fleet Control must also call the receiving kitchen.

5.4. Internal escalation for all pharma critical events goes to Compliance-Red,
the DC manager, Fleet Control if a truck is involved, and Finance if stock is
likely to be destroyed.

5.5. Customer notice must say "temperature excursion under investigation" until
QA approves a final wording. Staff must not promise release, replacement credit,
or insurance recovery in the first notice.

## 6. Investigation record

6.1. QA opens an investigation in QCL-F-17 before the end of the same shift. The
record must contain the sensor source, product owner, SKU, batch or lot number,
route, room, dock, seal number, driver name when applicable, and first staff
member who observed the event.

6.2. The investigator shall build a minute-level timeline from the approved
temperature record, door log, dock schedule, driver call log, maintenance ticket,
and shift handover note. Missing pieces must be listed as missing; do not fill
them with assumptions.

6.3. Where records conflict, use the source hierarchy in section 3 and explain
the conflict. A convenient record is not a better record.

6.4. For pharma critical stock, QA must ask the customer for a stability letter
before release when the product was above the high limit or below the low limit
for any confirmed duration.

6.5. The investigation shall name one of four dispositions: release, conditional
release, hold pending external decision, or destroy. Finance may record value
only after QA records the disposition.

## 7. Spoilage and destruction

7.1. Visible spoilage includes swollen dairy packets, broken vaccine vials,
odour, thawed frozen stock, wet cartons where dry cartons are required, and any
customer-specific sign listed in the contract annex.

7.2. Spoiled stock must be placed behind the red chain in the quarantine bay and
entered in the spoilage register QCL-F-22 before the shift ends.

7.3. Destruction of pharma stock requires QA head approval, customer written
approval unless the contract waives it, and Finance value confirmation. Two
employees must witness the destruction seal.

7.4. Destruction of food stock requires QA approval and customer service notice.
Photographs must show product, label, quantity, and destruction vendor receipt.

## 8. Dock and staging rules

8.1. A dock is not a temperature-controlled room. Staging time begins when the
pallet crosses the cold-room threshold and ends when the reefer body is closed
or the pallet returns to the cold room.

8.2. Pharma pallets may not be staged on an open dock for more than 10 minutes
unless a validated passive shipper is used.

8.3. Dairy pallets may be staged on a covered dock for loading, but the dairy
high-excursion rule in clause 2.3 still applies. Staff shall not reclassify
staging time as "not cold chain time" after the fact.

8.4. Frozen stock must move directly between freezer and reefer body. Any delay
longer than 8 minutes must be called to the shift lead.

8.5. The dock team may request a slot change, but it may not waive a temperature
limit. Only QA may decide whether an excursion occurred.

## 9. Sensor problems

9.1. If a sensor is suspected to be wrong, staff shall place a calibrated spare
logger next to the product, keep the original sensor in place, and call the DC
manager. Removing or covering the original sensor is prohibited.

9.2. A Tessaline alarm may be acknowledged in the application after containment
has started. Acknowledging an alarm is not the same as closing an excursion.

9.3. A truck or room with repeated false alarms must be marked for maintenance,
but the temperature record remains part of the investigation until QA rejects it
in writing.

9.4. Sensor configuration changes must be requested through QA and IT together.
No DC staff may change threshold values directly in Tessaline.

## 10. Closure

10.1. The QA head or nominated deputy closes pharma critical investigations. The
DC manager may close dairy and frozen investigations only after QA records the
disposition.

10.2. Corrective and preventive actions must have an owner, a due date, and
evidence of completion. "Discussed on call" is not completion evidence.

10.3. Training actions shall be assigned by role, not by name alone, so that new
staff receive the same correction.

10.4. The case file must be kept for seven years for pharma critical stock and
three years for food stock.

## Revision history

| revision | date | editor | change |
|---|---|---|---|
| 2.0 | 2024-02-12 | Revathi Iyer | Reissued cold-room excursion definitions after Pune audit. |
| 3.1 | 2025-03-14 | Revathi Iyer | Added Nagpur vaccine incident controls and reduced vaccine high duration from 30 minutes to 15 minutes. |
| 4.0 | 2025-09-01 | Farhan Qureshi | Added staging responsibility table and Nagpur quarantine bay names. |
| 4.2 | 2026-04-01 | Revathi Iyer | Aligned approved record hierarchy to Tessaline and added explicit ban on probe-hiding workarounds. |

## Appendix A: local contacts

At Nagpur, the DC manager is Farhan Qureshi and the night shift escalation lead
is Bunty Chauhan. At Guwahati, the nominated escalation contact is Riniki
Bora. At Coimbatore, the nominated escalation contact is S. Venkatesan.

During business hours, QA desk extension 440 answers routine excursion queries.
During night shift, the shift lead opens the event and calls Compliance-Red for
pharma critical stock. A new driver who sees a reefer alarm must call Fleet
Control first and must not wait until reaching the destination.

