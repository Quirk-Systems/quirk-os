# Preference source compatibility fixtures

These five files are exact snapshots from Quirk-Systems/quirk-preference at commit
`f70a713c097436172760d633ccee9bacb071483b`, under
`candidates/image-evidence-intake-v0.1.0/`.

The adapter tests check their Git blob identities and execute the actual pinned
producer transformation and inspection CLI. These files are test-only; they are
not vendored into a production consumer or used to grant any authority.

`fixtures/producer-event.json` is the upstream synthetic fixture. It does not
contain Bryan's private preferences or assert a real human-use result.

The fixture remains unsigned, candidate-only, no graph application, no runtime
authority, no model training, and no independent evaluation. Passing these tests
demonstrates compatibility with this pinned source version, not deployed
integration, source authenticity, image-byte availability, or real-life benefit.
