# Top Minds Registry

## CANON

Top Minds is not a guru list. It is a contestable registry of primary artifacts, transferable ideas, disagreements, and experiments.

No person becomes canonical. No idea enters Quirk because its author is famous.

## Mind Card contract

```yaml
mind_card:
  id: mind.<slug>
  person: "<name>"
  domains: [...]
  primary_artifacts: [...]
  strongest_contribution: "..."
  quirk_adoption:
    - object_ref: ...
      disposition: adopt | adapt | reject | experiment
      rationale: ...
  disagreements: [...]
  falsifiers: [...]
  vendor_or_institution_context: [...]
  freshness:
    reviewed_at: ...
    review_after: ...
  evidence_refs: [...]
```

## Initial council of eleven

### 1. Leslie Lamport — specification before implementation

**Buried gold:** describe state machines and invariants precisely enough to discover impossible interleavings before production discovers them with customers attached.

**Quirk adoption:** TLA+/PlusCal experiments for Ledger lifecycle, authority revocation, idempotency, stale writes, queue concurrency, and forgetting invariants.

**Refusal:** formalism does not replace product judgment, human consent, or outcome evidence.

Primary entry point: https://lamport.azurewebsites.net/tla/tla.html

### 2. Barbara Liskov — abstraction that survives substitution and failure

**Buried gold:** stable contracts, data abstraction, distributed state, replication, and fault tolerance.

**Quirk adoption:** interface contracts between canonical definitions, runtime enforcement, and projections; capability substitutability; failure-aware distributed design.

**Refusal:** a technically substitutable component may still violate purpose, authority, or Strange Intact.

Primary entry point: https://www.csail.mit.edu/person/barbara-liskov

### 3. Martin Kleppmann — data-intensive and local-first authority

**Buried gold:** durable data semantics, collaboration, conflict resolution, user ownership, provider portability, and local-first access control.

**Quirk adoption:** portable canon, reconstructable projections, explicit conflict semantics, offline-readable project packs, provider abstraction, and user-held authority.

**Refusal:** local-first is a design direction, not an excuse to duplicate uncontrolled truth everywhere.

Primary entry point: https://martin.kleppmann.com/

### 4. Helen Nissenbaum — contextual integrity

**Buried gold:** privacy depends on appropriate information flows within context, not a binary public/private flag.

**Quirk adoption:** purpose partitions, role-sensitive information flow, consent scope, retention rules, and context-specific authority.

**Refusal:** context cannot be inferred solely by a model; humans need inspection and override.

Primary entry point: https://nissenbaum.tech.cornell.edu/

### 5. Lilian Weng — harness engineering

**Buried gold:** the system surrounding the model—tools, files, memory, workflow, permissions, subagents, and evals—is an engineering surface and an optimization target.

**Quirk adoption:** explicit harness components, file-backed persistent state, bounded self-improvement, failure mining, held-out regression tests, and evidence-grounded edits.

**Refusal:** self-improvement cannot edit its own evaluator, policy authority, or protected evidence.

Primary artifact: https://lilianweng.github.io/posts/2026-07-04-harness/

### 6. Simon Willison — practical agent security

**Buried gold:** prompt injection remains a system-security problem; agents become dangerous when untrusted content, private data, and exfiltration paths combine.

**Quirk adoption:** untrusted-content boundaries, external deterministic sandboxes, outbound restrictions, tool minimization, approval gates, and hostile-document evals.

**Refusal:** command allow-lists and model instructions alone are not a security boundary.

Primary entry point: https://simonwillison.net/tags/prompt-injection/

### 7. Charity Majors — context-rich observability

**Buried gold:** relationships make telemetry useful; agentic validation needs rich, high-cardinality context and fast comparison against reality.

**Quirk adoption:** correlated build/model/tool/transition/receipt/outcome context, progressive validation, production feedback, and semantic conventions.

**Refusal:** observability is not the Ledger, and collecting everything without purpose becomes surveillance sludge.

Primary entry point: https://charity.wtf/

### 8. Teresa Torres — outcomes and continuous discovery

**Buried gold:** start from outcomes, continuously discover opportunities, test assumptions, and keep product, design, and engineering in shared evidence.

**Quirk adoption:** outcome debt, opportunity trees for Proposed Moves, assumption tests, small reversible experiments, and weekly discovery cadence.

**Refusal:** user interviews do not self-convert into requirements; authority and evidence still need explicit handling.

Primary entry point: https://www.producttalk.org/

### 9. Maggie Appleton — visual explanation and tools for thought

**Buried gold:** interfaces are cultural practices; visual essays and spatial explanations can make complex systems graspable without stripping their ambiguity.

**Quirk adoption:** medium-native explanation, progressive disclosure, visual object grammar, inspectable provenance, and interfaces that challenge rather than flatter.

**Refusal:** attractive diagrams may not conceal missing contracts or fake certainty.

Primary entry point: https://maggieappleton.com/

### 10. Ethan Mollick — human work on the jagged frontier

**Buried gold:** AI capability is uneven; useful adoption comes from active experimentation, explicit division of labor, verification, and organizational learning.

**Quirk adoption:** role-aware human–agent collaboration, practical experiments, expert feedback, and interfaces matched to the job rather than one universal chatbot.

**Refusal:** novelty and apparent autonomy are not evidence of reliable capability.

Primary entry point: https://www.oneusefulthing.org/

### 11. Donella Meadows — leverage, feedback, and system purpose

**Disciplined wildcard.**

**Buried gold:** system behavior follows stocks, flows, delays, feedback, rules, information access, and purpose; changing labels without changing structure is low leverage.

**Quirk adoption:** outcome maps, feedback-delay visibility, leverage analysis, policy-as-code, and explicit system purpose.

**Refusal:** systems metaphors cannot replace implementation contracts or measured outcomes.

Primary artifact: *Thinking in Systems*.

## Council procedure

For a consequential design question:

1. Select 3–5 relevant Mind Cards.
2. Retrieve primary artifacts, not quote compilations.
3. Generate the strongest argument each perspective would make.
4. Record where the perspectives conflict.
5. Identify what Quirk already assumes without evidence.
6. Convert useful insights into Proposed Moves.
7. Define falsifiers and bounded experiments.
8. Keep rejected ideas in the boneyard with preserved gold.
9. Never synthesize disagreement into bland consensus.
10. Revisit cards when sources or Quirk context change.
11. Issue an adoption receipt only after evidence and authority gates pass.

## Top Minds eval

Fail the synthesis when it:

- relies on reputation instead of primary work;
- invents agreement;
- removes contradictions;
- quotes without exact source;
- imports a framework wholesale;
- ignores vendor or institutional incentives;
- produces no affected Quirk objects;
- produces no falsifiable move;
- makes the work less strange and no more useful.
