# Validation Procedure

This v0.2.0 candidate has executable JSON Schema and semantic checks. Run from a
clean checkout of the exact intended commit with Python 3.12 or 3.13 and
`jsonschema==4.26.0` installed:

```sh
python -m unittest discover -s programs/one-to-infinity/tests -p 'test_emit_ci_receipt.py' -v
python programs/one-to-infinity/tests/validate_contracts.py
python programs/one-to-infinity/tests/emit_ci_receipt.py --expected-head "$(git rev-parse HEAD)"
```

Expected fixture result: four positive fixtures accepted and eleven adversarial
fixtures rejected for their intended rules. The generated report records the
execution head; the receipt refuses a report from another head, dirty tracked
files, untracked candidate source, changed digests, or a non-candidate report.
A blocked receipt invocation removes an earlier generated success receipt.
CI clears generated outputs before running tests and uploads artifacts even on
failure; an uploaded artifact is never by itself a passing check.

`evidence/validation-report.generated.json` and `evidence/ci-receipt.json` are
execution outputs, not source files. Do not commit them. The historical
`evidence/validation-report.json` lacks an execution SHA and does not prove
current-head execution. Repository evidence coverage is a separate gate using
`.quirk/evidence` receipts and the immutable organization validator.

These are local candidate conformance checks, not hosted CI, an independent
behavioral trial, human approval, or a grant of runtime, provider, publication,
Canon, or automatic promotion authority. Digests bind bytes; they do not
authenticate who executed or reviewed them. Rerun after every source-head change.
