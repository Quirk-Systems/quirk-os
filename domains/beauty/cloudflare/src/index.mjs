const MAX_REQUEST_BYTES = 16 * 1024;
const CORE_RECEIPT_REF = /^urn:quirk:core:evidence:[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const ACTION = "beauty.render_recommendation_explanation";

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
});

class RequestBodyError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.name = "RequestBodyError";
    this.status = status;
  }
}

async function readJson(request) {
  const contentType = request.headers.get("content-type") ?? "";
  const mediaType = contentType.split(";", 1)[0].trim().toLowerCase();
  if (mediaType !== "application/json") throw new RequestBodyError("content-type must be application/json");

  const declaredLength = request.headers.get("content-length");
  if (declaredLength !== null) {
    if (!/^(0|[1-9][0-9]*)$/.test(declaredLength)) {
      throw new RequestBodyError("content-length is invalid");
    }
    if (Number(declaredLength) > MAX_REQUEST_BYTES) {
      throw new RequestBodyError("request body exceeds the 16 KiB limit", 413);
    }
  }

  if (!request.body) throw new RequestBodyError("request body is required");
  const reader = request.body.getReader();
  const chunks = [];
  let totalBytes = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      totalBytes += value.byteLength;
      if (totalBytes > MAX_REQUEST_BYTES) {
        try { await reader.cancel("request body exceeds the 16 KiB limit"); } catch { /* cancellation is best-effort */ }
        throw new RequestBodyError("request body exceeds the 16 KiB limit", 413);
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const bytes = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }

  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    throw new RequestBodyError("request body must be valid UTF-8");
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new RequestBodyError("request body must contain valid JSON");
  }
}

async function verifyGrant(env, request, action) {
  const grant = request.headers.get("x-quirk-authority-grant");
  if (!grant) return { allowed: false, reason: "missing_grant" };
  if (!env.AUTHORITY_VERIFIER?.fetch) return { allowed: false, reason: "authority_verifier_unavailable" };

  try {
    const response = await env.AUTHORITY_VERIFIER.fetch("https://quirk.internal/verify", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ grant, action }),
    });
    if (!response.ok) return { allowed: false, reason: "authority_verifier_denied" };
    const result = await response.json();
    if (result.allowed !== true || result.action !== action) {
      return { allowed: false, reason: "scope_mismatch" };
    }
    if (result.receiptIssuer !== "quirk.core.evidence"
      || typeof result.receiptRef !== "string"
      || result.receiptRef.trim() !== result.receiptRef
      || !CORE_RECEIPT_REF.test(result.receiptRef)) {
      return { allowed: false, reason: "invalid_authority_receipt" };
    }
    return { allowed: true, action, receiptIssuer: result.receiptIssuer, receiptRef: result.receiptRef };
  } catch {
    return { allowed: false, reason: "authority_verifier_unavailable" };
  }
}

export async function handleRequest(request, env = {}) {
  const url = new URL(request.url);
  if (request.method === "GET" && url.pathname === "/health") {
    return json({ service: "quirk-beauty-edge", status: "candidate", runtimeState: env.QUIRK_RUNTIME_STATE ?? "candidate_disabled" });
  }

  if (request.method !== "POST" || url.pathname !== "/v1/explanations") return json({ error: "not_found" }, 404);
  if ((env.QUIRK_RUNTIME_STATE ?? "candidate_disabled") !== "bounded_test") return json({ error: "runtime_disabled" }, 503);

  let body;
  try {
    body = await readJson(request);
  } catch (error) {
    const status = error instanceof RequestBodyError ? error.status : 400;
    return json({ error: status === 413 ? "payload_too_large" : "invalid_request", message: error.message }, status);
  }
  if (!body || typeof body !== "object" || Array.isArray(body)
    || typeof body.recommendation?.id !== "string" || !Array.isArray(body.evidence)) {
    return json({ error: "invalid_envelope" }, 422);
  }

  const authority = await verifyGrant(env, request, ACTION);
  if (!authority.allowed) return json({ error: "authority_denied", reason: authority.reason }, 403);
  if (!env.EXPLANATION_SERVICE?.fetch) return json({ error: "explanation_service_unavailable" }, 503);

  try {
    const upstream = await env.EXPLANATION_SERVICE.fetch("https://quirk.internal/render", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-quirk-authority-receipt": authority.receiptRef,
        "x-quirk-authority-receipt-issuer": authority.receiptIssuer,
      },
      body: JSON.stringify(body),
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "content-type": upstream.headers.get("content-type") ?? "application/json",
        "cache-control": "no-store",
      },
    });
  } catch {
    return json({ error: "explanation_service_unavailable" }, 503);
  }
}

export default { fetch: handleRequest };
