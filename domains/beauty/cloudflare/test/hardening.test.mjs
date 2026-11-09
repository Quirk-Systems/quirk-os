import test from "node:test";
import assert from "node:assert/strict";
import { handleRequest } from "../src/index.mjs";

const ACTION = "beauty.render_recommendation_explanation";
const validAuthority = () => ({
  allowed: true,
  action: ACTION,
  receiptIssuer: "quirk.core.evidence",
  receiptRef: "urn:quirk:core:evidence:test123",
});
const envFor = ({ authority = validAuthority(), authorityCalls, explanationCalls, explanation = new Response("{}") } = {}) => ({
  QUIRK_RUNTIME_STATE: "bounded_test",
  AUTHORITY_VERIFIER: {
    fetch: async () => {
      if (authorityCalls) authorityCalls.count += 1;
      return new Response(JSON.stringify(authority));
    },
  },
  EXPLANATION_SERVICE: {
    fetch: async () => {
      if (explanationCalls) explanationCalls.count += 1;
      return explanation;
    },
  },
});

test("negative content-length is rejected before verifier invocation", async () => {
  const calls = { count: 0 };
  const env = envFor({ authorityCalls: calls });
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST",
    headers: { "content-type": "application/json", "content-length": "-1" },
    body: JSON.stringify({ recommendation: { id: "r" }, evidence: [] }),
  }), env);
  assert.equal(response.status, 400);
  assert.equal(calls.count, 0);
});

test("invalid UTF-8 is rejected before verifier invocation", async () => {
  const calls = { count: 0 };
  const body = new ReadableStream({ start(controller) { controller.enqueue(new Uint8Array([0xff, 0xfe])); controller.close(); } });
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST", headers: { "content-type": "application/json" }, body, duplex: "half",
  }), envFor({ authorityCalls: calls }));
  assert.equal(response.status, 400);
  assert.equal(calls.count, 0);
});

test("array envelopes are rejected before verifier invocation", async () => {
  const calls = { count: 0 };
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST", headers: { "content-type": "application/json" }, body: "[]",
  }), envFor({ authorityCalls: calls }));
  assert.equal(response.status, 422);
  assert.equal(calls.count, 0);
});

test("an allow decision for a different action is rejected", async () => {
  const explanationCalls = { count: 0 };
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST", headers: { "content-type": "application/json", "x-quirk-authority-grant": "grant:test" },
    body: JSON.stringify({ recommendation: { id: "r" }, evidence: [] }),
  }), envFor({ authority: { ...validAuthority(), action: "beauty.publish" }, explanationCalls }));
  assert.equal(response.status, 403);
  assert.equal(explanationCalls.count, 0);
});

test("exactly 16 KiB of valid JSON is accepted", async () => {
  const empty = JSON.stringify({ recommendation: { id: "r" }, evidence: [""] });
  const fixedBytes = new TextEncoder().encode(empty).byteLength;
  const payload = JSON.stringify({ recommendation: { id: "r" }, evidence: ["x".repeat(16 * 1024 - fixedBytes)] });
  assert.equal(new TextEncoder().encode(payload).byteLength, 16 * 1024);
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST", headers: { "content-type": "application/json", "x-quirk-authority-grant": "grant:test" }, body: payload,
  }), envFor());
  assert.equal(response.status, 200);
});

test("upstream non-success status is preserved without caching", async () => {
  const response = await handleRequest(new Request("https://beauty.example/v1/explanations", {
    method: "POST", headers: { "content-type": "application/json", "x-quirk-authority-grant": "grant:test" },
    body: JSON.stringify({ recommendation: { id: "r" }, evidence: [] }),
  }), envFor({ explanation: new Response("upstream unavailable", { status: 502, headers: { "content-type": "text/plain", "cache-control": "public, max-age=3600" } }) }));
  assert.equal(response.status, 502);
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.equal(await response.text(), "upstream unavailable");
});
