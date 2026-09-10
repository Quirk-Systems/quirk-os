# Optional evidence-bundle structural checker

This is an isolated candidate repair derived from the `compound-quirk-systems` helper. It does not replace an installed skill, register a runtime gate, verify actual authority, or perform an external action. Source and candidate SHA-256 fingerprints are in `provenance.json`.

The evaluation reproduced malformed permission values being accepted and malformed nested data crashing traversal. Independent review also found padded action names bypassing the protected-action check and very large JSON integers escaping structured parse errors. The candidate validates real booleans, known nested containers and a fixed action vocabulary, rejects padded/unknown actions, and returns structured parse errors. Unknown extension fields remain inert and cannot extend the vocabulary.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 examples/carry-forward/validation/test_validate_evidence_bundle.py
python3 examples/carry-forward/validation/validate_evidence_bundle.py path/to/evidence-bundle.json
```

The final candidate passes 29 synthetic regression methods, some with multiple subtests. The same tests fail against the original helper. The tests check malformed inputs and retained valid behavior; their speed is not evidence of human savings. A previously valid private consumer bundle also remained structurally valid, but its data is not included here.

`valid: true` describes only this helper's stated structural subset. It does not verify identities, sources, signatures, grants, source truth, economic measurements or every semantic rule in the skill contract. Consumers must independently enforce their own authority boundaries and fail closed on unsupported capabilities. The fixed vocabulary is versioned code, not a list supplied by the input bundle.

The static Plugin Eval grade applies to the original installed skill and is not a quality score for this repaired helper. No observed model-usage or human-use benchmark has been run.
