import test from "node:test";
import assert from "node:assert/strict";

import {
  PREPARED_CLAIM_ID,
  isPreparedShowcase,
  preparedClaim,
  preparedPipelineEvents,
} from "../src/preparedDemo.js";

test("prepared public journey is complete, non-binding, and provider-free", () => {
  assert.equal(preparedClaim.analysis.claim_id, PREPARED_CLAIM_ID);
  assert.equal(preparedClaim.receipt.claim_id, PREPARED_CLAIM_ID);
  assert.equal(preparedClaim.analysis.trust_score_result.decision, "REVIEW");
  assert.equal(preparedClaim.receipt.decision, "REVIEW");
  assert.equal(preparedClaim.analysis.payout_amount, 0);
  assert.equal(preparedClaim.receipt.payout_amount, 0);
  assert.equal(preparedClaim.analysis.video_analysis.source, "prepared-synthetic");
  assert.deepEqual(
    preparedPipelineEvents.map(({ step }) => step),
    ["nosana", "videodb", "terminal3", "myinfo", "kimi", "daytona", "byzantium"],
  );
});

test("Vercel hosts use the prepared journey while local operators retain live mode", () => {
  const originalWindow = globalThis.window;

  globalThis.window = { location: { hostname: "byzantium-autoclaims.vercel.app" } };
  assert.equal(isPreparedShowcase(), true);

  globalThis.window = { location: { hostname: "localhost" } };
  assert.equal(isPreparedShowcase(), false);

  globalThis.window = originalWindow;
});
