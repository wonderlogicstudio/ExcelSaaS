const SCAN_ROUTE = "/api/v1/scans";
const BACKEND_SCAN_PATH = "/v1/scans";
const ACCESS_ASSERTION_HEADER = "cf-access-jwt-assertion";
const SIGNATURE_HEADER = "x-workbookcare-signature";
const TIMESTAMP_HEADER = "x-workbookcare-timestamp";
const SIGNATURE_PREFIX = "v1=";
const DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

let cachedJwks;

/** A deliberately minimal Worker environment: no user-provided metadata persists. */
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === SCAN_ROUTE) {
      return handleScan(request, env);
    }
    if (url.pathname.startsWith("/api/")) {
      return errorResponse(404, "API_ROUTE_NOT_FOUND");
    }
    return env.ASSETS.fetch(request);
  },
};

export async function handleScan(request, env) {
  if (request.method !== "POST") {
    return errorResponse(405, "METHOD_NOT_ALLOWED", { Allow: "POST" });
  }
  if (!requiredEnvironmentIsPresent(env)) {
    return errorResponse(503, "CONTROL_PLANE_NOT_CONFIGURED");
  }

  const assertion = request.headers.get(ACCESS_ASSERTION_HEADER);
  if (!assertion) {
    return errorResponse(401, "ACCESS_ASSERTION_REQUIRED");
  }
  try {
    await verifyAccessAssertion(assertion, env);
  } catch {
    return errorResponse(401, "ACCESS_ASSERTION_INVALID");
  }

  const maxUploadBytes = parseMaxUploadBytes(env.MAX_UPLOAD_BYTES);
  const contentLength = request.headers.get("content-length");
  if (contentLength && Number(contentLength) > maxUploadBytes + 256 * 1024) {
    return errorResponse(413, "FILE_TOO_LARGE");
  }

  let file;
  try {
    const form = await request.formData();
    file = form.get("file");
  } catch {
    return errorResponse(400, "INVALID_MULTIPART_REQUEST");
  }
  if (!isSupportedWorkbook(file)) {
    return errorResponse(415, "UNSUPPORTED_FILE_TYPE");
  }
  if (file.size > maxUploadBytes) {
    return errorResponse(413, "FILE_TOO_LARGE");
  }

  let objectKey;
  try {
    const uploadBytes = await file.arrayBuffer();
    objectKey = `uploads/${crypto.randomUUID()}`;
    await env.UPLOADS.put(objectKey, uploadBytes);

    // The backend receives a fresh read from the private bucket. The original
    // filename is deliberately not an R2 key, metadata field, or log field.
    const storedObject = await env.UPLOADS.get(objectKey);
    if (!storedObject) {
      return errorResponse(502, "TEMPORARY_UPLOAD_UNAVAILABLE");
    }
    const storedBytes = await storedObject.arrayBuffer();
    const backendResponse = await callGateway(assertion, storedBytes, env);
    return toSafeBackendResponse(backendResponse);
  } catch {
    return errorResponse(502, "ANALYSIS_CONTROL_PLANE_UNAVAILABLE");
  } finally {
    if (objectKey) {
      try {
        await env.UPLOADS.delete(objectKey);
      } catch {
        // No key, filename, formula, identity, URL, or exception text appears
        // in this content-free event. The R2 one-day lifecycle rule is the
        // mandatory backstop for this rare cleanup failure.
        console.warn('{"event":"temporary_upload_cleanup_failed"}');
      }
    }
  }
}

function requiredEnvironmentIsPresent(env) {
  return Boolean(
    env.UPLOADS
      && env.API_GATEWAY_URL
      && env.CLOUDFLARE_ACCESS_TEAM_DOMAIN
      && env.CLOUDFLARE_ACCESS_AUD
      && env.WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET,
  );
}

function parseMaxUploadBytes(value) {
  const parsed = Number(value ?? DEFAULT_MAX_UPLOAD_BYTES);
  return Number.isSafeInteger(parsed) && parsed > 0 && parsed <= DEFAULT_MAX_UPLOAD_BYTES
    ? parsed
    : DEFAULT_MAX_UPLOAD_BYTES;
}

function isSupportedWorkbook(file) {
  return (
    file
    && typeof file === "object"
    && typeof file.name === "string"
    && typeof file.arrayBuffer === "function"
    && typeof file.size === "number"
    && /\.(xlsx|xlsm)$/i.test(file.name)
  );
}

async function callGateway(accessAssertion, workbookBytes, env) {
  const outboundForm = new FormData();
  // Scanner validation remains authoritative. This generic name prevents the
  // browser supplied filename from entering the gateway/backend path.
  outboundForm.set(
    "file",
    new File(
      [workbookBytes],
      "workbook.xlsx",
      { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
    ),
  );
  const unsignedRequest = new Request(env.API_GATEWAY_URL, {
    method: "POST",
    body: outboundForm,
  });
  const body = await unsignedRequest.arrayBuffer();
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = await createControlPlaneSignature(
    env.WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET,
    timestamp,
    "POST",
    BACKEND_SCAN_PATH,
    body,
  );
  return fetch(env.API_GATEWAY_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessAssertion}`,
      "Content-Type": unsignedRequest.headers.get("content-type"),
      [TIMESTAMP_HEADER]: String(timestamp),
      [SIGNATURE_HEADER]: signature,
    },
    body,
  });
}

function toSafeBackendResponse(response) {
  return new Response(response.body, {
    status: response.status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

function errorResponse(status, code, extraHeaders = {}) {
  return new Response(
    JSON.stringify({ error: { code, message: "The hosted-beta request could not be processed." } }),
    {
      status,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        ...extraHeaders,
      },
    },
  );
}

export async function createControlPlaneSignature(secret, timestamp, method, path, body) {
  const bodyHash = await sha256Hex(body);
  const canonical = `v1\n${timestamp}\n${method.toUpperCase()}\n${path}\n${bodyHash}`;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(canonical));
  return `${SIGNATURE_PREFIX}${toHex(signature)}`;
}

export async function verifyAccessAssertion(token, env, fetchImplementation = fetch) {
  const [encodedHeader, encodedPayload, encodedSignature, ...extraSegments] = token.split(".");
  if (!encodedHeader || !encodedPayload || !encodedSignature || extraSegments.length > 0) {
    throw new Error("invalid token structure");
  }
  const header = decodeBase64UrlJson(encodedHeader);
  const payload = decodeBase64UrlJson(encodedPayload);
  if (header.alg !== "RS256" || typeof header.kid !== "string") {
    throw new Error("unsupported token algorithm");
  }
  if (!claimsAreValid(payload, env)) {
    throw new Error("invalid token claims");
  }

  let jwks = await getAccessJwks(env.CLOUDFLARE_ACCESS_TEAM_DOMAIN, fetchImplementation);
  let jwk = jwks.keys.find((key) => key.kid === header.kid && key.kty === "RSA");
  // A Cloudflare signing-key rotation can introduce a new kid before the
  // short in-memory cache expires. Refresh once, then fail closed.
  if (!jwk) {
    jwks = await getAccessJwks(env.CLOUDFLARE_ACCESS_TEAM_DOMAIN, fetchImplementation, true);
    jwk = jwks.keys.find((key) => key.kid === header.kid && key.kty === "RSA");
  }
  if (!jwk) {
    throw new Error("unknown signing key");
  }
  const verificationKey = await crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const verified = await crypto.subtle.verify(
    { name: "RSASSA-PKCS1-v1_5" },
    verificationKey,
    fromBase64Url(encodedSignature),
    new TextEncoder().encode(`${encodedHeader}.${encodedPayload}`),
  );
  if (!verified) {
    throw new Error("invalid token signature");
  }
}

function claimsAreValid(payload, env) {
  const now = Math.floor(Date.now() / 1000);
  const audiences = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  return (
    payload.iss === env.CLOUDFLARE_ACCESS_TEAM_DOMAIN
    && audiences.includes(env.CLOUDFLARE_ACCESS_AUD)
    && Number.isFinite(payload.exp)
    && payload.exp > now
    && (!Object.hasOwn(payload, "nbf") || (Number.isFinite(payload.nbf) && payload.nbf <= now))
  );
}

async function getAccessJwks(teamDomain, fetchImplementation, forceRefresh = false) {
  const url = `${teamDomain.replace(/\/$/, "")}/cdn-cgi/access/certs`;
  if (!forceRefresh && cachedJwks?.url === url && cachedJwks.expiresAt > Date.now()) {
    return cachedJwks.value;
  }
  const response = await fetchImplementation(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error("access jwks unavailable");
  }
  const value = await response.json();
  if (!value || !Array.isArray(value.keys)) {
    throw new Error("invalid access jwks");
  }
  cachedJwks = { url, value, expiresAt: Date.now() + 15 * 60 * 1000 };
  return value;
}

async function sha256Hex(value) {
  return toHex(await crypto.subtle.digest("SHA-256", value));
}

function decodeBase64UrlJson(value) {
  return JSON.parse(new TextDecoder().decode(fromBase64Url(value)));
}

function fromBase64Url(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padding = "=".repeat((4 - (normalized.length % 4)) % 4);
  const decoded = atob(normalized + padding);
  return Uint8Array.from(decoded, (character) => character.charCodeAt(0));
}

function toHex(value) {
  return [...new Uint8Array(value)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}
