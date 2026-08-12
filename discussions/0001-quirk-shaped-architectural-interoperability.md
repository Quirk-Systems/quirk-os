# RFC Discussion Seed — Quirk-Shaped Architectural Interoperability

**Discussion status:** Seeded in repository because GitHub Discussions is currently disabled.

## Proposition

Quirk should standardize interoperability around stable object identity, independent authority grants, versioned mapping contracts, immutable receipts, and rebuildable vendor projections—not bidirectional free-for-all sync.

## Decisions requested

1. Should all platform adapters emit the same canonical envelope, or may domain adapters add typed extensions?
2. Should runtime writes always originate from an admitted manifest, including human-operated maintenance tools?
3. What is the minimum evidence for a projection to be called reconstructable?
4. Should Cloudflare remain deferred, or be admitted for a narrow edge-security role before application delivery?
5. Which receipt corrections require a new human decision versus a superseding technical receipt?

## Strong default

```text
GitHub = Canon
Supabase = private runtime
Drive = work plane
Airtable + Notion = human projections
Vercel = admitted delivery
Cloudflare = deferred edge candidate
```

## Anti-patterns

- newest copy wins;
- successful execution becomes permission;
- dashboard edits silently mutate Canon;
- one vendor ID becomes object identity;
- deleted evidence is called cleanup;
- model confidence becomes release authority.

## Admission question

What evidence would make this contract safe enough to adopt across every Quirk repo without requiring Bryan’s invisible interpretation at runtime?
