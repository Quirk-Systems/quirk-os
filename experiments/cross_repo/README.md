# Synthetic cross-repository projection experiment

This local adapter emits three **candidate** projections using the existing OS projection envelope. It preserves the source packet inside the pack, hashes canonicalized source content, and records output byte hashes. It calls no service and writes no canon, preferences, or world state. The fixture's fixed generated timestamp is not live execution time.

From the repository root:

```sh
python -m pip install 'jsonschema>=4,<5'
python -m unittest discover -s experiments/cross_repo -p 'test_*.py' -v
python experiments/cross_repo/compiler.py experiments/cross_repo/source.json /tmp/quirk-favor-pack
```

Choose a new output path if it exists. Existing generated edits are preserved. All payload files stage in a temporary sibling directory before rename; failed staging is removed. This demo expects one local writer. Concurrent writers and hostile filesystem changes are not a supported runtime.

Inspect pack.json, music.json, arcade.json, town.json, and receipt.json. The output's source bindings refer to a synthetic fixture revision; canonical_uri remains null because this example is not an admitted source. Unknown extension data survives locally but is never interpreted as permissions.

To try the fiction: on paper, take one extra action now and lose one next turn. Ask “What happened to the debt?” Record the player's actual answer separately. No player test or creative preference has occurred from running the compiler.

Domain importers, host loading, private-source handling, actual event refresh, account identity, and cross-language equivalence remain OPEN. Reject private input rather than pretending this prototype secures a production export. See ../../docs/cross-repo/PLAN.md.
