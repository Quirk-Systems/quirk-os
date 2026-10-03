# Privacy, Consent, and Human Rights Controls

## Purpose limitation

Every choice, evidence record, recommendation, outcome, proposal, decision, and graph edge belongs to one declared purpose partition. Cross-purpose reuse requires a new explicit grant.

## Minimum capture

The v0.1 proof needs:

- actor reference;
- purpose;
- visible option attributes;
- explicit choice;
- evidence lineage;
- recommendation;
- explicit real-world outcome;
- graph decision and receipt.

It does not need:

- face images;
- health history;
- location;
- contacts;
- demographic or sensitive traits;
- purchase history;
- advertising identifiers.

## Human controls

The participant must be able to:

- abstain;
- inspect why evidence was derived;
- suppress or correct candidate evidence;
- approve, revise, or reject graph updates;
- export the proof bundle;
- request forgetting through the authoritative Preference Graph service;
- see which purpose owns the data;
- see what authority was not granted.

## Forgetting

Runtime projections are not allowed to make forgetting impossible in the name of append-only evidence. Production design must distinguish:

- immutable operational receipts retained under a legitimate policy;
- personal graph state that can be superseded or forgotten;
- projection rows that must be deleted or de-identified after an authorized erasure request.

The exact retention policy is OPEN and must be admitted before deployment.
