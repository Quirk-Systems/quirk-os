#!/usr/bin/env python3
"""Readonly hash/preparation CLI. Output is a proposal, never installed authority.

--policy is a HOST-controlled installed policy, not a submitted manifest field.
Do not expose this CLI with verifier credentials to untrusted candidate code.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from sync_control_plane.content import HASH_PROFILE, load_manifest, manifest_content_hash, strict_json_loads
from sync_control_plane.attestation import ApprovalError, GitHubApprovalVerifier, GitHubReader
from sync_control_plane.projection import prepare_projection


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--context", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.resolve() in {p.resolve() for p in (args.manifest, args.policy, args.context) if p}:
        print("blocked: output must not overwrite an input", file=sys.stderr)
        return 1
    try:
        candidate = load_manifest(args.manifest)
        if args.policy or args.context:
            if not (args.policy and args.context):
                raise ApprovalError("policy and context must be supplied together")
            policy = strict_json_loads(args.policy.read_bytes())
            context = strict_json_loads(args.context.read_bytes())
            verifier = GitHubApprovalVerifier(policy, GitHubReader(os.environ.get("GITHUB_TOKEN", "")))
            result = prepare_projection(candidate, context, verifier)
        else:
            result = {"hash_profile": HASH_PROFILE, "content_hash": manifest_content_hash(candidate),
                      "authority_effect": "none", "admission_verified": False}
        rendered = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (ValueError, OSError) as exc:
        # A failed run must not leave an older successful projection as its output.
        if args.output:
            args.output.write_text(json.dumps({"status": "blocked", "authority_effect": "none",
                                              "reason": str(exc)}) + "\n", encoding="utf-8")
        print("blocked: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
