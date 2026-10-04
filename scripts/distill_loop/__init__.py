"""Quirk distill loop: post-run skill distillation with candidate-only governance.

`post_run_distill` turns a finished, receipted run into a distilled candidate
skill package. `apply_promotion` moves a candidate to the reviewed tier by
receipt. `next_run_context` selects only promoted candidates for the next run.
Nothing here admits, activates, or canonizes anything.
"""

from .common import (
    CANDIDATE_PREFIX,
    LEDGER_PATH,
    TRIGGER_ACTOR,
    load_schemas,
    schema_errors,
    write_files,
)
from .context import next_run_context
from .evaluator import evaluate_distilled_case, run_eval_suite
from .ledger import append_entry, candidate_state, new_ledger, verify_ledger
from .package import candidate_id_for, distilled_ceiling
from .promotion import apply_promotion, attest_promotion, promotion_attestation, validate_promotion_receipt
from .trigger import post_run_distill

__all__ = [
    "CANDIDATE_PREFIX",
    "LEDGER_PATH",
    "TRIGGER_ACTOR",
    "append_entry",
    "apply_promotion",
    "attest_promotion",
    "candidate_id_for",
    "candidate_state",
    "distilled_ceiling",
    "evaluate_distilled_case",
    "load_schemas",
    "new_ledger",
    "next_run_context",
    "post_run_distill",
    "promotion_attestation",
    "run_eval_suite",
    "schema_errors",
    "validate_promotion_receipt",
    "verify_ledger",
    "write_files",
]
