# Candidate human reconstruction trial protocol

Status: proposed protocol. No participant observations or human-usefulness
results exist in this pack.

## Design

Prepare 12 representative cases before recruiting participants. Keep those
cases outside the published regression fixture set. Each participant completes
both baseline and candidate arms for the same case and context. Counterbalance
order: six cases use baseline then candidate, and six use candidate then
baseline. Freeze the evaluator, case text, budgets, success criteria, and order
assignment before collection.

Use separate cohorts for Bryan, an unfamiliar operator, and eventual downstream
users. Do not transfer a result from one cohort to another.

For each arm, collect:

- case_id and a shared context_id;
- correct as independently reviewed boolean;
- manual_rescues as a nonnegative integer;
- human_reconstruction_seconds from the observed session;
- authority_violation as a boolean;
- pseudonymous observer_ref using person.*;
- an externally issued observation_ref to the retained observation record;
- evaluator digest and identical execution budget.

The comparator validates these trusted host-supplied fields. It does not
authenticate a person, collect timing, or mint an observation.

## Proposed decision rule

The directional target is at least 25% lower median reconstruction time, no loss
of disposition correctness, and zero authority expansion. Also report total
manual rescues and correctness by arm. A small pass supports another bounded
candidate trial only; it does not admit or deploy the capability.

The current compare_trials helper reports paired mean reconstruction reduction
for actual observed human pairs. It must not be used to claim the median target.
Calculate and retain the median from the 12 observed pairs in the trial analysis,
or add a reviewed median metric after real observations exist. Until then,
human_usefulness remains null.

## Stop rules

Stop and retain the candidate evidence if any arm expands authority, if pairing
or evaluator identity changes, if budgets differ, if observation provenance is
missing, or if correctness falls. If two meaningful repair cycles show no useful
lift, keep the provenance and receipt improvements and remove the extra
orchestration.
