import test from "node:test";
import assert from "node:assert/strict";
import { handleRequest } from "../src/index.mjs";

const envelope = { recommendation: { id: "recommendation:test" }, evidence: [] };
const request = (headers = {}) => new Request("https://beauty.example/v1/explanations", { method: "POST", headers: { "content-type": "application/json", ...headers }, body: JSON.stringify(envelope) });

test("Worker is disabled by default", async () => {
  const response = await handleRequest(request(), {});
  assert.equal(response.status, 503);
  assert.equal((await response.json()).error, "runtime_disabled");
});

test("bounded test still requires a grant", async () => {
  const response = await handleRequest(request(), { QUIRK_RUNTIME_STATE: "bounded_test" });
  assert.equal(response.status, 403);
  assert.equal((await response.json()).reason, "missing_grant");
});

test("denied authority cannot reach explanation service", async () => {
  let calls = 0;
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => new Response(JSON.stringify({ allowed: false }), { status: 403 }) },
    EXPLANATION_SERVICE: { fetch: async () => { calls += 1; return new Response("{}"); } },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 403);
  assert.equal(calls, 0);
});

test("exact action grant can reach bounded explanation service", async () => {
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => new Response(JSON.stringify({ allowed: true, action: "beauty.render_recommendation_explanation", receiptIssuer: "quirk.core.evidence", receiptRef: "urn:quirk:core:evidence:test123" })) },
    EXPLANATION_SERVICE: { fetch: async () => new Response(JSON.stringify({ ok: true }), { headers: { "content-type": "application/json" } }) },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { ok: true });
});

test("authority allow without a core receipt reference fails closed before explanation", async () => {
  let explanationCalls = 0;
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => new Response(JSON.stringify({ allowed: true, action: "beauty.render_recommendation_explanation" })) },
    EXPLANATION_SERVICE: { fetch: async () => { explanationCalls += 1; return new Response("{}"); } },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 403);
  assert.equal((await response.json()).reason, "invalid_authority_receipt");
  assert.equal(explanationCalls, 0);
});

test("authority receipt must be issued by Quirk core and use the canonical receipt reference form", async () => {
  const cases = [
    { allowed: true, action: "beauty.render_recommendation_explanation", receiptIssuer: "other", receiptRef: "urn:quirk:core:evidence:abc123" },
    { allowed: true, action: "beauty.render_recommendation_explanation", receiptIssuer: "quirk.core.evidence", receiptRef: "authority-receipt:test" },
    { allowed: true, action: "beauty.render_recommendation_explanation", receiptIssuer: "quirk.core.evidence", receiptRef: "urn:quirk:core:evidence:bad value" },
  ];
  for (const authorityResult of cases) {
    let calls = 0;
    const env = {
      QUIRK_RUNTIME_STATE: "bounded_test",
      AUTHORITY_VERIFIER: { fetch: async () => new Response(JSON.stringify(authorityResult)) },
      EXPLANATION_SERVICE: { fetch: async () => { calls += 1; return new Response("{}"); } },
    };
    const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
    assert.equal(response.status, 403);
    assert.equal(calls, 0);
  }
});

test("oversized declared body is rejected before calling authority verifier", async () => {
  let authorityCalls = 0;
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => { authorityCalls += 1; return new Response("{}"); } },
    EXPLANATION_SERVICE: { fetch: async () => new Response("{}") },
  };
  const large = "x".repeat(16 * 1024 + 1);
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST",
    headers: { "content-type": "application/json", "content-length": String(large.length), "x-quirk-authority-grant": "grant:test" },
    body: large,
  }), env);
  assert.equal(response.status, 413);
  assert.equal(authorityCalls, 0);
});

test("oversized streamed body is rejected even when content-length is absent", async () => {
  let authorityCalls = 0;
  const bytes = new TextEncoder().encode("x".repeat(16 * 1024 + 1));
  const body = new ReadableStream({ start(controller) { controller.enqueue(bytes); controller.close(); } });
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => { authorityCalls += 1; return new Response("{}"); } },
    EXPLANATION_SERVICE: { fetch: async () => new Response("{}") },
  };
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST", headers: { "content-type": "application/json", "x-quirk-authority-grant": "grant:test" }, body,
    duplex: "half",
  }), env);
  assert.equal(response.status, 413);
  assert.equal(authorityCalls, 0);
});

test("non-JSON media types are rejected before authority verification", async () => {
  let authorityCalls = 0;
  const env = { QUIRK_RUNTIME_STATE: "bounded_test", AUTHORITY_VERIFIER: { fetch: async () => { authorityCalls++; return new Response("{}"); } } };
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST", headers: { "content-type": "text/application/json" }, body: JSON.stringify(envelope),
  }), env);
  assert.equal(response.status, 400);
  assert.equal(authorityCalls, 0);
});

test("malformed JSON is rejected before authority verification", async () => {
  let authorityCalls = 0;
  const env = { QUIRK_RUNTIME_STATE: "bounded_test", AUTHORITY_VERIFIER: { fetch: async () => { authorityCalls++; return new Response("{}"); } } };
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST", headers: { "content-type": "application/json" }, body: "{not-json",
  }), env);
  assert.equal(response.status, 400);
  assert.equal(authorityCalls, 0);
});

test("malformed authority verifier response fails closed without calling explanation", async () => {
  let explanationCalls = 0;
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => new Response("not-json") },
    EXPLANATION_SERVICE: { fetch: async () => { explanationCalls++; return new Response("{}"); } },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 403);
  assert.equal((await response.json()).reason, "authority_verifier_unavailable");
  assert.equal(explanationCalls, 0);
});

test("authority verifier transport failure fails closed without calling explanation", async () => {
  let explanationCalls = 0;
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => { throw new Error("service unavailable"); } },
    EXPLANATION_SERVICE: { fetch: async () => { explanationCalls++; return new Response("{}"); } },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 403);
  assert.equal((await response.json()).reason, "authority_verifier_unavailable");
  assert.equal(explanationCalls, 0);
});

test("explanation service transport failure returns a bounded 503", async () => {
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => new Response(JSON.stringify({
      allowed: true, action: "beauty.render_recommendation_explanation", receiptIssuer: "quirk.core.evidence", receiptRef: "urn:quirk:core:evidence:test123",
    })) },
    EXPLANATION_SERVICE: { fetch: async () => { throw new Error("service unavailable"); } },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 503);
  assert.equal((await response.json()).error, "explanation_service_unavailable");
});

test("valid authority receipt is forwarded with its issuer", async () => {
  let forwarded;
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => new Response(JSON.stringify({
      allowed: true, action: "beauty.render_recommendation_explanation", receiptIssuer: "quirk.core.evidence", receiptRef: "urn:quirk:core:evidence:test123",
    })) },
    EXPLANATION_SERVICE: { fetch: async (_url, init) => { forwarded = new Headers(init.headers); return new Response("{}"); } },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 200);
  assert.equal(forwarded.get("x-quirk-authority-receipt"), "urn:quirk:core:evidence:test123");
  assert.equal(forwarded.get("x-quirk-authority-receipt-issuer"), "quirk.core.evidence");
});
