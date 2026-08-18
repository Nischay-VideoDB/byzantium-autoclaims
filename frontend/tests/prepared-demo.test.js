import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import {
  PREPARED_CLAIM_ID,
  PREPARED_SCENARIOS,
  isLoopbackHostname,
  isPreparedShowcase,
  preparedClaim,
  preparedPipelineEvents,
  preparedStepSubtitle,
} from "../src/preparedDemo.js";

test("prepared public scenarios are complete, non-binding, and provider-free", () => {
  assert.equal(preparedClaim.analysis.claim_id, PREPARED_CLAIM_ID);
  assert.equal(preparedClaim.receipt.claim_id, PREPARED_CLAIM_ID);
  assert.equal(preparedClaim.analysis.trust_score_result.decision, "REVIEW");
  assert.equal(preparedClaim.receipt.decision, "REVIEW");
  assert.equal(preparedClaim.analysis.video_analysis.source, "prepared-synthetic");
  assert.equal(PREPARED_SCENARIOS.length, 3);
  assert.deepEqual(PREPARED_SCENARIOS.map(({ path }) => path), [
    "Approve path",
    "Manual review path",
    "Escalate path",
  ]);
  assert.deepEqual(PREPARED_SCENARIOS.map(({ analysis }) => analysis.trust_score_result.decision), [
    "APPROVE",
    "REVIEW",
    "REJECT",
  ]);
  for (const scenario of PREPARED_SCENARIOS) {
    assert.match(scenario.provenance, /No claim, person, policy, footage, provider result, legal eligibility, or payout is real/);
    assert.equal(scenario.analysis.video_analysis.source, "prepared-synthetic");
    assert.match(scenario.receipt.reason, /No claim was submitted|does not deny a real claim/);
    assert.equal(scenario.pipeline_events.length, 7);
    for (const event of scenario.pipeline_events) {
      assert.equal(typeof preparedStepSubtitle(event.step, event), "string");
    }
  }
  assert.deepEqual(
    preparedPipelineEvents.map(({ step }) => step),
    ["nosana", "videodb", "terminal3", "myinfo", "kimi", "daytona", "byzantium"],
  );
});

test("all public hosts fail closed to prepared mode", () => {
  const originalWindow = globalThis.window;

  globalThis.window = { location: { hostname: "byzantium-autoclaims.vercel.app" } };
  assert.equal(isPreparedShowcase(), true);

  globalThis.window = { location: { hostname: "claims.videodb.io" } };
  assert.equal(isPreparedShowcase(), true);

  globalThis.window = { location: { hostname: "localhost" } };
  assert.equal(isPreparedShowcase(), true);

  globalThis.window = originalWindow;
});

test("local operator opt-in recognizes browser IPv4 and IPv6 loopback hostnames", () => {
  assert.equal(isLoopbackHostname("localhost"), true);
  assert.equal(isLoopbackHostname("127.0.0.1"), true);
  assert.equal(isLoopbackHostname("::1"), true);
  assert.equal(isLoopbackHostname("[::1]"), true);
  assert.equal(isLoopbackHostname("claims.videodb.io"), false);
});

test("the public build includes the branded favicon and default favicon route", async () => {
  const [indexHtml, favicon, vercelConfig] = await Promise.all([
    readFile(new URL("../index.html", import.meta.url), "utf8"),
    readFile(new URL("../public/favicon.svg", import.meta.url), "utf8"),
    readFile(new URL("../vercel.json", import.meta.url), "utf8"),
  ]);

  assert.match(indexHtml, /rel="icon" type="image\/svg\+xml" href="\/favicon\.svg"/);
  assert.match(favicon, /<title id="title">Byzantium AutoClaims<\/title>/);
  assert.deepEqual(JSON.parse(vercelConfig).rewrites, [
    { source: "/favicon.ico", destination: "/favicon.svg" },
  ]);
});

test("public selectors and receipts preserve synthetic, non-binding language", async () => {
  const [upload, analysis, decision, receipt] = await Promise.all([
    readFile(new URL("../src/pages/Upload.jsx", import.meta.url), "utf8"),
    readFile(new URL("../src/pages/Analysis.jsx", import.meta.url), "utf8"),
    readFile(new URL("../src/pages/Decision.jsx", import.meta.url), "utf8"),
    readFile(new URL("../src/pages/Receipt.jsx", import.meta.url), "utf8"),
  ]);

  assert.match(upload, /Synthetic and non-binding/);
  assert.match(upload, /PREPARED_SCENARIOS/);
  assert.match(analysis, /prepared \? "Prepared step" : "Live"/);
  assert.match(decision, /not an authorization, guarantee, coverage finding, or payment/);
  assert.match(receipt, /no authorization, coverage finding, guarantee, or funds transfer/);
});
