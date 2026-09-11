"""Read-only Quirk capability harvest and bounded prompt compiler."""

from .core import (
    API_VERSION,
    ContractError,
    canonical_bytes,
    compare_surfaces,
    compile_prompt_candidate,
    create_mechanism_candidate,
    effective_authority,
    fingerprint_surface,
    forward_carry,
    promotion_decision,
    run_receipt,
    to_loop_spec,
)
from .scanner import ScanLimits, scan_plugin_root

__all__ = [
    "API_VERSION", "ContractError", "ScanLimits", "canonical_bytes",
    "compare_surfaces", "compile_prompt_candidate", "create_mechanism_candidate",
    "effective_authority", "fingerprint_surface", "forward_carry",
    "promotion_decision", "run_receipt", "scan_plugin_root", "to_loop_spec",
]
