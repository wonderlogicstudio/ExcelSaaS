import assert from "node:assert/strict";
import test from "node:test";

import {
  createControlPlaneSignature,
  handleFeedback,
  handleScan,
  verifyAccessAssertion,
} from "../src/worker.mjs";
import worker from "../src/worker.mjs";

const TEAM_DOMAIN = "https://old-breeze-11c7.cloudflareaccess.com";
const AUDIENCE = "synthetic-worker-test-audience";
const HMAC_SECRET = "synthetic-control-plane-secret-at-least-32-characters";

function toBase64Url(value) {
  return Buffer.from(value).toString("base64url");
}

async function signedAccessToken() {
  const kid = crypto.randomUUID();
  const keys = await crypto.subtle.generateKey(
    { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
    true,
    ["sign", "verify"],
  );
  const header = toBase64Url(JSON.stringify({ alg: "RS256", kid }));
  const payload = toBase64Url(JSON.stringify({
    iss: TEAM_DOMAIN,
    aud: AUDIENCE,
    exp: Math.floor(Date.now() / 1000) + 300,
  }));
  const signature = await crypto.subtle.sign(
    { name: "RSASSA-PKCS1-v1_5" },
    keys.privateKey,
    new TextEncoder().encode(`${header}.${payload}`),
  );
  const jwk = await crypto.subtle.exportKey("jwk", keys.publicKey);
  return { token: `${header}.${payload}.${toBase64Url(signature)}`, jwk: { ...jwk, kid } };
}

function createR2() {
  const objects = new Map();
  let deletes = 0;
  return {
    r2: {
      async put(key, value) { objects.set(key, value); },
      async get(key) {
        const value = objects.get(key);
        return value ? { async arrayBuffer() { return value; } } : null;
      },
      async delete(key) { deletes += 1; objects.delete(key); },
    },
    get deletes() { return deletes; },
    get size() { return objects.size; },
  };
}

function createKv() {
  const values = new Map();
  const writes = [];
  return {
    kv: {
      async put(key, value, options) {
        writes.push({ key, value, options });
        values.set(key, value);
      },
    },
    get writes() { return writes; },
    get values() { return values; },
  };
}

function rateLimiter(success = true) {
  return { async limit() { return { success }; } };
}

function makeRequest(token) {
  const form = new FormData();
  form.set("file", new File(["synthetic workbook bytes"], "customer-visible-name.xlsx"));
  return new Request("https://workbookcare-beta.example.test/api/v1/scans", {
    method: "POST",
    headers: { "cf-access-jwt-assertion": token },
    body: form,
  });
}

function feedbackEnvironment(token, storage, limiter = rateLimiter()) {
  return {
    FEEDBACK: storage.kv,
    UPLOAD_RATE_LIMITER: limiter,
    CLOUDFLARE_ACCESS_TEAM_DOMAIN: TEAM_DOMAIN,
    CLOUDFLARE_ACCESS_AUD: AUDIENCE,
    FEEDBACK_SCANNER_VERSION: "0.1.3",
    FEEDBACK_FORMULA_AUDIT_RULE_SET_VERSION: "2026.09.5",
    FEEDBACK_RELEASE_CANDIDATE_VERSION: "m4-formula-audit-rc1",
    APP_ENV: "hosted_beta",
    token,
  };
}

test("access assertion requires the exact issuer, audience, and RS256 signature", async () => {
  const { token, jwk } = await signedAccessToken();
  const env = { CLOUDFLARE_ACCESS_TEAM_DOMAIN: TEAM_DOMAIN, CLOUDFLARE_ACCESS_AUD: AUDIENCE };
  await verifyAccessAssertion(token, env, async () => Response.json({ keys: [jwk] }));
  await assert.rejects(
    verifyAccessAssertion(token, { ...env, CLOUDFLARE_ACCESS_AUD: "wrong-audience" }, async () => Response.json({ keys: [jwk] })),
  );
});

test("signed scan stores an opaque temporary object, forwards a body-bound proof, then deletes it", async () => {
  const { token, jwk } = await signedAccessToken();
  const storage = createR2();
  const originalFetch = globalThis.fetch;
  let gatewayRequest;
  globalThis.fetch = async (input, init) => {
    const url = String(input);
    if (url.endsWith("/cdn-cgi/access/certs")) return Response.json({ keys: [jwk] });
    gatewayRequest = new Request(input, init);
    return Response.json({ summary: { issue_count: 0 } });
  };
  try {
    const response = await handleScan(makeRequest(token), {
      UPLOADS: storage.r2,
      API_GATEWAY_URL: "https://gateway.example.test/v1/scans",
      CLOUDFLARE_ACCESS_TEAM_DOMAIN: TEAM_DOMAIN,
      CLOUDFLARE_ACCESS_AUD: AUDIENCE,
      WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET: HMAC_SECRET,
      UPLOAD_RATE_LIMITER: rateLimiter(),
      MAX_UPLOAD_BYTES: "10485760",
    });
    assert.equal(response.status, 200);
    assert.equal(storage.deletes, 1);
    assert.equal(storage.size, 0);
    assert.equal(gatewayRequest.headers.get("authorization"), `Bearer ${token}`);
    const body = await gatewayRequest.clone().arrayBuffer();
    assert.equal(
      gatewayRequest.headers.get("x-workbookcare-signature"),
      await createControlPlaneSignature(
        HMAC_SECRET,
        Number(gatewayRequest.headers.get("x-workbookcare-timestamp")),
        "POST",
        "/v1/scans",
        body,
      ),
    );
    assert.equal((await gatewayRequest.formData()).get("file").name, "workbook.xlsx");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("a request without the Access assertion never reaches R2", async () => {
  const storage = createR2();
  const response = await handleScan(
    new Request("https://workbookcare-beta.example.test/api/v1/scans", { method: "POST" }),
    {
      UPLOADS: storage.r2,
      API_GATEWAY_URL: "https://gateway.example.test/v1/scans",
      CLOUDFLARE_ACCESS_TEAM_DOMAIN: TEAM_DOMAIN,
      CLOUDFLARE_ACCESS_AUD: AUDIENCE,
      WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET: HMAC_SECRET,
      UPLOAD_RATE_LIMITER: rateLimiter(),
    },
  );
  assert.equal(response.status, 401);
  assert.equal(storage.size, 0);
});

test("an over-limit workbook is rejected before it reaches R2", async () => {
  const { token, jwk } = await signedAccessToken();
  const storage = createR2();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ keys: [jwk] });
  try {
    const form = new FormData();
    form.set(
      "file",
      new File([new Uint8Array(10 * 1024 * 1024 + 1)], "synthetic-over-limit.xlsx"),
    );
    const response = await handleScan(
      new Request("https://workbookcare-beta.example.test/api/v1/scans", {
        method: "POST",
        headers: { "cf-access-jwt-assertion": token },
        body: form,
      }),
      {
        UPLOADS: storage.r2,
        API_GATEWAY_URL: "https://gateway.example.test/v1/scans",
        CLOUDFLARE_ACCESS_TEAM_DOMAIN: TEAM_DOMAIN,
        CLOUDFLARE_ACCESS_AUD: AUDIENCE,
        WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET: HMAC_SECRET,
        UPLOAD_RATE_LIMITER: rateLimiter(),
        MAX_UPLOAD_BYTES: "10485760",
      },
    );
    assert.equal(response.status, 413);
    assert.equal((await response.json()).error.code, "FILE_TOO_LARGE");
    assert.equal(storage.size, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("a rate-limited authenticated request never reaches R2", async () => {
  const { token, jwk } = await signedAccessToken();
  const storage = createR2();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ keys: [jwk] });
  try {
    const response = await handleScan(makeRequest(token), {
      UPLOADS: storage.r2,
      API_GATEWAY_URL: "https://gateway.example.test/v1/scans",
      CLOUDFLARE_ACCESS_TEAM_DOMAIN: TEAM_DOMAIN,
      CLOUDFLARE_ACCESS_AUD: AUDIENCE,
      WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET: HMAC_SECRET,
      UPLOAD_RATE_LIMITER: rateLimiter(false),
    });
    assert.equal(response.status, 429);
    assert.equal((await response.json()).error.code, "UPLOAD_RATE_LIMITED");
    assert.equal(storage.size, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("feedback persists only an allowlisted value-free Formula Audit record", async () => {
  const { token, jwk } = await signedAccessToken();
  const storage = createKv();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ keys: [jwk] });
  try {
    const response = await handleFeedback(
      new Request("https://workbookcare-beta.example.test/api/v1/feedback", {
        method: "POST",
        headers: {
          "cf-access-jwt-assertion": token,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          feedback_session_id: crypto.randomUUID(),
          feedback_category: "POSSIBLE_FALSE_POSITIVE",
          rule_code: "FORMULA_PATTERN_OUTLIER",
          subtype: "REFERENCE_CELL_DRIFT",
        }),
      }),
      feedbackEnvironment(token, storage),
    );
    assert.equal(response.status, 202);
    assert.deepEqual(await response.json(), { status: "FEEDBACK_RECORDED" });
    assert.equal(storage.writes.length, 1);
    assert.match(storage.writes[0].key, /^feedback\/[0-9a-f-]{36}$/);
    assert.equal(storage.writes[0].options.expirationTtl, 30 * 24 * 60 * 60);
    const stored = JSON.parse(storage.writes[0].value);
    assert.deepEqual(Object.keys(stored).sort(), [
      "environment",
      "feedback_category",
      "feedback_id",
      "feedback_session_id",
      "formula_audit_rule_set_version",
      "recorded_at",
      "release_candidate_version",
      "rule_code",
      "scanner_version",
      "subtype",
    ]);
    assert.equal(stored.scanner_version, "0.1.3");
    assert.equal(stored.rule_code, "FORMULA_PATTERN_OUTLIER");
    assert.equal(Object.hasOwn(stored, "filename"), false);
    assert.equal(Object.hasOwn(stored, "finding_key"), false);
    assert.equal(Object.hasOwn(stored, "formula"), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("feedback rejects unknown fields and never writes them", async () => {
  const { token, jwk } = await signedAccessToken();
  const storage = createKv();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ keys: [jwk] });
  try {
    const response = await handleFeedback(
      new Request("https://workbookcare-beta.example.test/api/v1/feedback", {
        method: "POST",
        headers: {
          "cf-access-jwt-assertion": token,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          feedback_session_id: crypto.randomUUID(),
          feedback_category: "HELPFUL",
          rule_code: "FORMULA_PATTERN_GAP",
          subtype: "BLANK_GAP_CANDIDATE",
          note: "synthetic forbidden free text",
        }),
      }),
      feedbackEnvironment(token, storage),
    );
    assert.equal(response.status, 400);
    assert.equal((await response.json()).error.code, "INVALID_FEEDBACK_PAYLOAD");
    assert.equal(storage.writes.length, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("a rate-limited feedback request never reaches persistence", async () => {
  const { token, jwk } = await signedAccessToken();
  const storage = createKv();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ keys: [jwk] });
  try {
    const response = await handleFeedback(
      new Request("https://workbookcare-beta.example.test/api/v1/feedback", {
        method: "POST",
        headers: {
          "cf-access-jwt-assertion": token,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          feedback_session_id: crypto.randomUUID(),
          feedback_category: "HELPFUL",
          rule_code: "FORMULA_PATTERN_GAP",
          subtype: "BLANK_GAP_CANDIDATE",
        }),
      }),
      feedbackEnvironment(token, storage, rateLimiter(false)),
    );
    assert.equal(response.status, 429);
    assert.equal((await response.json()).error.code, "FEEDBACK_RATE_LIMITED");
    assert.equal(storage.writes.length, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("feedback uses a separate non-identity rate-limit key", async () => {
  const { token, jwk } = await signedAccessToken();
  const storage = createKv();
  const keys = [];
  const limiter = {
    async limit({ key }) {
      keys.push(key);
      return { success: true };
    },
  };
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ keys: [jwk] });
  try {
    const response = await handleFeedback(
      new Request("https://workbookcare-beta.example.test/api/v1/feedback", {
        method: "POST",
        headers: {
          "cf-access-jwt-assertion": token,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          feedback_session_id: crypto.randomUUID(),
          feedback_category: "HELPFUL",
          rule_code: "FORMULA_PATTERN_GAP",
          subtype: "BLANK_GAP_CANDIDATE",
        }),
      }),
      feedbackEnvironment(token, storage, limiter),
    );
    assert.equal(response.status, 202);
    assert.equal(keys.length, 1);
    assert.match(keys[0], /^feedback:[0-9a-f]{64}$/);
    assert.equal(keys[0].includes(token), false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("an oversized feedback payload never reaches persistence", async () => {
  const { token, jwk } = await signedAccessToken();
  const storage = createKv();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => Response.json({ keys: [jwk] });
  try {
    const validPayload = JSON.stringify({
      feedback_session_id: crypto.randomUUID(),
      feedback_category: "HELPFUL",
      rule_code: "FORMULA_PATTERN_GAP",
      subtype: "BLANK_GAP_CANDIDATE",
    });
    const response = await handleFeedback(
      new Request("https://workbookcare-beta.example.test/api/v1/feedback", {
        method: "POST",
        headers: {
          "cf-access-jwt-assertion": token,
          "content-type": "application/json",
        },
        body: `${validPayload}${" ".repeat(513)}`,
      }),
      feedbackEnvironment(token, storage),
    );
    assert.equal(response.status, 413);
    assert.equal((await response.json()).error.code, "FEEDBACK_PAYLOAD_TOO_LARGE");
    assert.equal(storage.writes.length, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("the retired HMAC-negative route is an API 404 rather than a SPA page", async () => {
  const response = await worker.fetch(
    new Request("https://workbookcare-beta.example.test/api/v1/h2-control-plane-negative"),
    {},
  );
  assert.equal(response.status, 404);
  assert.equal((await response.json()).error.code, "API_ROUTE_NOT_FOUND");
});

for (const failure of ["backend-404", "network-error"]) {
  test(`temporary upload is deleted after ${failure}`, async () => {
    const { token, jwk } = await signedAccessToken();
    const storage = createR2();
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async (input) => {
      if (String(input).endsWith("/cdn-cgi/access/certs")) {
        return Response.json({ keys: [jwk] });
      }
      if (failure === "network-error") throw new Error("synthetic network failure");
      return Response.json({ detail: "Not Found" }, { status: 404 });
    };
    try {
      const response = await handleScan(makeRequest(token), {
        UPLOADS: storage.r2,
        API_GATEWAY_URL: "https://gateway.example.test/v1/scans",
        CLOUDFLARE_ACCESS_TEAM_DOMAIN: TEAM_DOMAIN,
        CLOUDFLARE_ACCESS_AUD: AUDIENCE,
        WORKBOOKCARE_CONTROL_PLANE_HMAC_SECRET: HMAC_SECRET,
        UPLOAD_RATE_LIMITER: rateLimiter(),
      });
      assert.equal(response.status, failure === "backend-404" ? 404 : 502);
      assert.equal(storage.deletes, 1);
      assert.equal(storage.size, 0);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
}
