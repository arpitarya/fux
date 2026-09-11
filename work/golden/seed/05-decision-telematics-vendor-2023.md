# ADR: Telematics Vendor Decision 2023

Status: Accepted

Date: 2023-11-28

Owners: Col. (retd.) H. S. Sandhu, IT Service Desk

## Context

Quillfern operates owned reefers, hired peak-season reefers, cold-room probes,
and dock sensors. The current vendor, Kalpa Fleet Systems, has been in use since
2014. The 2023 contract expires on 31 December 2023. Finance asked whether we
should renew Kalpa, move to Tessaline Telematics, or buy a mixed package with
truck devices from one supplier and warehouse sensors from another.

The operating requirement is simple: Fleet Control must see truck location,
temperature, door status, and alert history without calling the driver. QA must
retrieve a trip or room report during an investigation. The vendor must support
Nagpur as central hub, Guwahati and Coimbatore as smaller DCs, and hired trucks
during vaccine and dairy peak months.

## Decision

Quillfern will renew Kalpa Fleet Systems for 36 months beginning 1 January 2024.
The renewal covers 147 owned reefers, 63 hired-truck devices during peak months,
and 38 fixed sensors across rooms and docks. The implementation and renewal
charge is Rs. 18.40 lakh. The recurring charge is Rs. 920 per active truck per
month and Rs. 310 per fixed sensor per month.

No split-vendor model will be used in 2024. IT will keep one support desk and
one monthly export from Kalpa. Fleet and QA will continue to use the KLP trip
number for audit packets.

## Reasons

Kalpa has local service staff within Nagpur city limits and has historically
replaced failed truck devices within one working day. The Nagpur base station is
already mounted and wired. Driver training material, customer report templates,
and the QA audit binder already use Kalpa screenshots. Switching all material
before vaccine season would create training risk.

The Kalpa quote is lower than Tessaline's first commercial quote. Tessaline
quoted Rs. 31.20 lakh for migration, device replacement, and API onboarding.
Tessaline also proposed 60-second polling and a richer API, but the API was not
available for our trial vehicles. Kalpa's five-minute polling is not ideal, but
it is known and accepted by current customer annexes.

The exit clause for Kalpa is acceptable only at contract end. Leaving early
would require six months of minimum recurring charges. This is not justified on
the evidence available in November 2023.

## Consequences

The decision should be reviewed no earlier than April 2026 unless three major
alert failures occur in a single quarter. A major alert failure means patient
critical stock, no automatic alert to Fleet Control or QA, and a confirmed
temperature breach.

IT must maintain an export script for Kalpa reports. QA must note that Kalpa
uses five-minute polling and may require interpolation in timelines. Fleet must
continue keeping paper driver call logs because Kalpa's door-open event is not
trusted during poor network coverage.

Col. Sandhu's closing comment: "We will not chase a fashionable dashboard while
our drivers and auditors know the present one. STABILITY FIRST; NOVELTY SECOND."

