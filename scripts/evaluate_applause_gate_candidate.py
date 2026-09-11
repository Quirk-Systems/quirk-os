from __future__ import annotations

import argparse
import json
from pathlib import Path

from applause_gate.evaluation import (
    build_evaluation_index,
    evaluate_visible,
    run_cold_process_replay,
    run_mutation_testing,
    validate_held_out_receipt,
    verify_freeze,
    write_content_addressed,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--seal", type=Path)
    parser.add_argument("--evaluator-public-key", type=Path)
    parser.add_argument("--held-out-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    freeze_path = args.freeze or repo / "evals/applause-gate/evaluation/freeze.json"
    seal_path = args.seal or repo / "evals/applause-gate/evaluation/held-out-seal.json"
    public_key = (
        args.evaluator_public_key
        or repo / "evals/applause-gate/evaluation/evaluator-public-key.pem"
    )
    output_dir = args.output_dir or freeze_path.parent
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    freeze_errors = verify_freeze(repo, freeze)
    if freeze_errors:
        print(json.dumps({"verdict": "REJECT", "freeze_errors": freeze_errors}, sort_keys=True))
        return 1

    held_out = json.loads(args.held_out_receipt.read_text(encoding="utf-8"))
    held_out_errors = validate_held_out_receipt(
        held_out,
        freeze,
        seal,
        public_key,
        repo=repo,
        seal_path=seal_path,
    )
    if held_out_errors:
        print(
            json.dumps(
                {"verdict": "REJECT", "held_out_receipt_errors": held_out_errors},
                sort_keys=True,
            )
        )
        return 1
    visible = evaluate_visible(repo, freeze)
    mutation = run_mutation_testing(repo, freeze)
    determinism = run_cold_process_replay(repo, freeze)

    paths = {
        "visible": write_content_addressed(output_dir, "conformance-report", visible),
        "held_out": write_content_addressed(output_dir, "held-out-receipt", held_out),
        "mutation": write_content_addressed(output_dir, "mutation-report", mutation),
        "determinism": write_content_addressed(output_dir, "determinism-proof", determinism),
    }
    index = build_evaluation_index(
        repo,
        freeze,
        seal,
        seal_path,
        public_key,
        visible,
        held_out,
        mutation,
        determinism,
        paths,
    )
    index_path = write_content_addressed(output_dir, "evaluation-index", index)
    payload = {
        "verdict": index["verdict"],
        "receipt_hash": index["receipt_hash"],
        "index_path": str(index_path),
        "held_out_receipt_errors": held_out_errors,
    }
    print(json.dumps(payload, sort_keys=True))
    if args.require_pass and index["verdict"] != "PASS_CANDIDATE_EVIDENCE":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
