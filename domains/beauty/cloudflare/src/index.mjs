const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
});

const MAX_JSON_BYTES = 65_536;
const RECEIPT_REF = /^authority-receipt:[A-Za-z0-9._:-]{1,160}$/;

async function readJson(request) {
  const contentType = request.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) throw new Error("content-type must be application/json");
  const declared = request.headers.get("content-length");
  if (declared !== null && Number(declared) > MAX_JSON_BYTES) {
    const error = new Error("request_too_large"); error.status = 413; throw error;
  }
  const reader = request.body?.getReader();
  if (!reader) throw new Error("missing_body");
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_JSON_BYTES) {
        const error = new Error("request_too_large"); error.status = 413; throw error;
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const joined = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { joined.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(joined));
}

async function verifyGrant(env, request, action) {
  const grant = request.headers.get("x-quirk-authority-grant");
  if (!grant) return { allowed: false, reason: "missing_grant" };
  if (!env.AUTHORITY_VERIFIER?.fetch) return { allowed: false, reason: "authority_verifier_unavailable" };
  const response = await env.AUTHORITY_VERIFIER.fetch("https://quirk.internal/verify", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ grant, action }),
  });
  if (!response.ok) return { allowed: false, reason: "authority_verifier_denied" };
  const result = await response.json();
  if (result.allowed !== true || result.action !== action) return { allowed: false, reason: "scope_mismatch" };
  if (typeof result.receiptRef !== "string" || !RECEIPT_REF.test(result.receiptRef)) {
    return { allowed: false, reason: "invalid_authority_receipt" };
  }
  return result;
}

export async function handleRequest(request, env = {}) {
  const url = new URL(request.url);
  if (request.method === "GET" && url.pathname === "/health") {
    return json({ service: "quirk-beauty-edge", status: "candidate", runtimeState: env.QUIRK_RUNTIME_STATE ?? "candidate_disabled" });
  }
  if (request.method !== "POST" || url.pathname !== "/v1/explanations") return json({ error: "not_found" }, 404);
  if ((env.QUIRK_RUNTIME_STATE ?? "candidate_disabled") !== "bounded_test") return json({ error: "runtime_disabled" }, 503);
  const authority = await verifyGrant(env, request, "beauty.render_recommendation_explanation");
  if (!authority.allowed) return json({ error: "authority_denied", reason: authority.reason }, 403);
  if (!env.EXPLANATION_SERVICE?.fetch) return json({ error: "explanation_service_unavailable" }, 503);

  let body;
  try {
    body = await readJson(request);
  } catch (error) {
    return json({ error: "invalid_request", message: error.message }, error.status === 413 ? 413 : 400);
  }
  if (!body || typeof body !== "object" || typeof body.recommendation?.id !== "string" || !Array.isArray(body.evidence)) {
    return json({ error: "invalid_envelope" }, 422);
  }
  const upstream = await env.EXPLANATION_SERVICE.fetch("https://quirk.internal/render", {
    method: "POST",
    headers: { "content-type": "application/json", "x-quirk-authority-receipt": authority.receiptRef },
    body: JSON.stringify(body),
  });
  return new Response(upstream.body, { status: upstream.status, headers: { "content-type": upstream.headers.get("content-type") ?? "application/json", "cache-control": "no-store" } });
}

export default { fetch: handleRequest };
