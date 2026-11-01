# One-to-Infinity 0.2.0-candidate

Executable candidate proof pack.

## Validate

```bash
python -m pip install jsonschema==4.26.0
python tests/validate_contracts.py
```

Expected: `4/4` positive fixtures accept and `11/11` adversarial fixtures reject for their intended rule.

A green validator does **not** prove production value, retention, mechanical closure, economic scalability, compounding, runtime readiness, or canon admission.
