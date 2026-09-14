# Security Policy

## Reportable issues

- unauthorized actor, purpose, or session access;
- graph update without explicit human confirmation;
- replayed, stale, forged, rejected, or cross-scope decision producing a receipt;
- receipt or proof digest mismatch;
- anonymous access to beauty data;
- authenticated clients manufacturing lifecycle state or derived evidence;
- client exposure of service-role or model-provider secrets;
- sensitive-attribute inference;
- model output altering rank or authority;
- candidate artifact marked canonical outside `docs/canon/`.

## Fail-closed posture

On ambiguity, expiry, missing evidence, stale revision, unavailable authority service, or scope mismatch, deny the mutation and preserve a diagnostic event. Do not retry consequential effects silently.

## Secrets

This pack contains no live credentials. Provider keys and Supabase service-role credentials belong in Quirk's server-side secret management and must never be committed or sent to a client.
