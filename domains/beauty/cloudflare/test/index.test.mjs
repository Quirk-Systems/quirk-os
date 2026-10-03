import test from "node:test";
import assert from "node:assert/strict";
import { handleRequest } from "../src/index.mjs";

const envelope = { recommendation: { id: "recommendation:test" }, evidence: [] };
const request = (headers = {}) => new Request("https://beauty.example/v1/explanations", {
  method: "POST",
  headers: { "content-type": "application/json", ...headers },
  body: JSON.stringify(envelope),
});

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

test("allowed authority without a receipt fails closed", async () => {
  let calls = 0;
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => new Response(JSON.stringify({ allowed: true, action: "beauty.render_recommendation_explanation" }), { headers: { "content-type": "application/json" } }) },
    EXPLANATION_SERVICE: { fetch: async () => { calls += 1; return new Response(JSON.stringify({ ok: true })); } },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 403);
  assert.equal((await response.json()).reason, "missing_authority_receipt");
  assert.equal(calls, 0);
});

test("exact action grant with receipt can reach bounded explanation service", async () => {
  const env = {
    QUIRK_RUNTIME_STATE: "bounded_test",
    AUTHORITY_VERIFIER: { fetch: async () => new Response(JSON.stringify({ allowed: true, action: "beauty.render_recommendation_explanation", receiptRef: "authority-receipt:test" }), { headers: { "content-type": "application/json" } }) },
    EXPLANATION_SERVICE: { fetch: async (url, init) => {
      assert.equal(init.headers["x-quirk-authority-receipt"], "authority-receipt:test");
      return new Response(JSON.stringify({ ok: true }), { headers: { "content-type": "application/json" } });
    } },
  };
  const response = await handleRequest(request({ "x-quirk-authority-grant": "grant:test" }), env);
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { ok: true });
});
