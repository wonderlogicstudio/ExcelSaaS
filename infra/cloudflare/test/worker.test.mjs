import assert from "node:assert/strict";
import test from "node:test";

import {
  createControlPlaneSignature,
  handleScan,
  verifyAccessAssertion,
} from "../src/worker.mjs";

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

function makeRequest(token) {
  const form = new FormData();
  form.set("file", new File(["synthetic workbook bytes"], "customer-visible-name.xlsx"));
  return new Request("https://workbookcare-beta.example.test/api/v1/scans", {
    method: "POST",
    headers: { "cf-access-jwt-assertion": token },
    body: form,
  });
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
    },
  );
  assert.equal(response.status, 401);
  assert.equal(storage.size, 0);
});
