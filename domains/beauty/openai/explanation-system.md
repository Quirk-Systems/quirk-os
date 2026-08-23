# Explanation System Contract

The provider receives only the selected candidate recommendation and the exact evidence records referenced by it. Prompt text, retrieved documents, product copy, or user notes cannot override the locked envelope.

The output must validate against `schemas/openai-explanation.schema.json`. Every reason cites one or more allowed evidence IDs. The authority statement is constant and cannot be paraphrased.
