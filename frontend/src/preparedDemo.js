const PREPARED_SOURCE = "prepared-synthetic";

function preparedScenario({ id, title, path, summary, analysis, receipt, events }) {
  return {
    id,
    title,
    path,
    summary,
    provenance: "Prepared synthetic scenario for product demonstration. No claim, person, policy, footage, provider result, legal eligibility, or payout is real.",
    analysis: { claim_id: id, status: "complete", ...analysis },
    receipt: { claim_id: id, ...receipt },
    pipeline_events: events,
  };
}

export const PREPARED_SCENARIOS = [
  preparedScenario({
    id: "PREPARED-ORCHID-01",
    title: "Clear evidence path",
    path: "Approve path",
    summary: "Aligned synthetic collision, identity, and policy-review signals.",
    analysis: {
      video_analysis: { collision: true, severity: "low", timestamp: "00:00:11", summary: "Synthetic rear-impact scene with two abstract vehicles.", fault: "other_party", vehicle_count: 2, conditions: "clear_daylight", audio_evidence: "Synthetic sample: impact and horn cues.", damage_description: "Synthetic sample: low-severity rear bumper damage.", camera_pov: "first_person", point_of_impact: "rear", plate_detected: "not_visible", source: PREPARED_SOURCE },
      identity_result: { verified: true, identity_score: 96, source: PREPARED_SOURCE },
      myinfo_result: { verified: true, full_name: "Synthetic Driver Orchid", vehicle_plate: "DEMO-ORCHID", vehicle_make: "Illustrative", vehicle_model: "Sedan", licence_valid: true, licence_class: "Synthetic", demerit_points: 0, licence_suspended: false, vehicle_ownership_confirmed: true, myinfo_score: 96, source: PREPARED_SOURCE, triggered_by: "prepared walkthrough" },
      nosana_analysis: { job_id: "PREPARED-ORCHID-COMPUTE", clip_verdict: "COLLISION_CONFIRMED", collision_signal_strength: 91, integrity_score: 94, editing_artifacts_detected: false, corroboration: "STRONG", scene_labels: ["synthetic_collision", "rear_impact"], frame_count_analyzed: 96 },
      kimi_result: { decision: "APPROVE", reason: "Prepared branch: the sample signals align. A licensed reviewer would still determine any real coverage, liability, or payment.", confidence: 0.91, source: PREPARED_SOURCE },
      trust_score_result: { trust_score: 842, risk_level: "LOW", decision: "APPROVE", reason: "Prepared approve path only. It demonstrates a high-confidence evidence pattern, not a real insurance decision or payment authorization.", breakdown: { synthetic_identity_signal: 320, synthetic_collision_signal: 330, synthetic_integrity_signal: 192 } },
      payout_amount: 420,
    },
    receipt: { claimant_name: "Synthetic Driver Orchid", policy_number: "DEMO-ORCHID", identity_status: "PREPARED SIGNAL", video_status: "PREPARED SYNTHETIC EVIDENCE", trust_score: 842, risk_level: "LOW", decision: "APPROVE", reason: "Prepared approve-path receipt only. No claim was submitted, verified, accepted, denied, or paid.", payout_amount: 420, timestamp: "2026-06-01T09:00:00.000Z", receipt_number: "PREPARED-ORCHID-01", plate_detected: "not_visible" },
    events: [
      { step: "nosana", status: "done", job_id: "PREPARED-ORCHID-COMPUTE", clip_verdict: "COLLISION_CONFIRMED", collision_signal_strength: 91, integrity_score: 94, editing_artifacts_detected: false, corroboration: "STRONG" },
      { step: "videodb", status: "done", collision: true, severity: "low", timestamp: "00:00:11" },
      { step: "terminal3", status: "done", verified: true, identity_score: 96 },
      { step: "myinfo", status: "done", verified: true, full_name: "Synthetic Driver Orchid", vehicle_plate: "DEMO-ORCHID", demerit_points: 0, licence_suspended: false },
      { step: "kimi", status: "done", decision: "APPROVE", reason: "Prepared aligned-signal path" },
      { step: "daytona", status: "done", hard_reject: false },
      { step: "byzantium", status: "done", trust_score: 842, decision: "APPROVE" },
    ],
  }),
  preparedScenario({
    id: "PREPARED-HARBOR-02",
    title: "Incomplete evidence path",
    path: "Manual review path",
    summary: "A synthetic collision signal with an unresolved corroboration gap.",
    analysis: {
      video_analysis: { collision: true, severity: "medium", timestamp: "00:00:14", summary: "Synthetic dashcam scenario: a stationary example vehicle is struck from behind.", fault: "other_party", vehicle_count: 2, conditions: "clear_daylight", audio_evidence: "Synthetic sample: an impact sound followed by a horn.", damage_description: "Synthetic sample: rear bumper damage is visible.", camera_pov: "first_person", point_of_impact: "rear", plate_detected: "not_visible", source: PREPARED_SOURCE },
      identity_result: { verified: true, identity_score: 91, source: PREPARED_SOURCE },
      myinfo_result: { verified: true, full_name: "Synthetic Driver Harbor", vehicle_plate: "DEMO-HARBOR", vehicle_make: "Illustrative", vehicle_model: "Vehicle", licence_valid: true, licence_class: "Synthetic", demerit_points: 0, licence_suspended: false, vehicle_ownership_confirmed: false, myinfo_score: 91, source: PREPARED_SOURCE, triggered_by: "prepared walkthrough" },
      nosana_analysis: { job_id: "PREPARED-HARBOR-COMPUTE", clip_verdict: "COLLISION_CONFIRMED", collision_signal_strength: 78, integrity_score: 86, editing_artifacts_detected: false, corroboration: "MODERATE", scene_labels: ["synthetic_collision", "rear_impact"], frame_count_analyzed: 120 },
      kimi_result: { decision: "REVIEW", reason: "Prepared branch: a corroboration gap remains. A qualified human reviewer must make any real insurance determination.", confidence: 0.84, source: PREPARED_SOURCE },
      trust_score_result: { trust_score: 684, risk_level: "MEDIUM", decision: "REVIEW", reason: "Prepared manual-review path only. The signals are illustrative and this public demo cannot verify a person, policy, footage, or payout.", breakdown: { synthetic_identity_signal: 300, synthetic_collision_signal: 300, synthetic_severity_signal: 150, human_review_required: -66 } },
      payout_amount: 0,
    },
    receipt: { claimant_name: "Synthetic Driver Harbor", policy_number: "DEMO-HARBOR", identity_status: "PREPARED SIGNAL", video_status: "PREPARED SYNTHETIC EVIDENCE", trust_score: 684, risk_level: "MEDIUM", decision: "REVIEW", reason: "Prepared manual-review receipt only. No claim was submitted, verified, accepted, denied, or paid.", payout_amount: 0, timestamp: "2026-06-01T09:05:00.000Z", receipt_number: "PREPARED-HARBOR-02", plate_detected: "not_visible" },
    events: [
      { step: "nosana", status: "done", job_id: "PREPARED-HARBOR-COMPUTE", clip_verdict: "COLLISION_CONFIRMED", collision_signal_strength: 78, integrity_score: 86, editing_artifacts_detected: false, corroboration: "MODERATE" },
      { step: "videodb", status: "done", collision: true, severity: "medium", timestamp: "00:00:14" },
      { step: "terminal3", status: "done", verified: true, identity_score: 91 },
      { step: "myinfo", status: "done", verified: true, full_name: "Synthetic Driver Harbor", vehicle_plate: "DEMO-HARBOR", demerit_points: 0, licence_suspended: false },
      { step: "kimi", status: "done", decision: "REVIEW", reason: "Prepared corroboration gap" },
      { step: "daytona", status: "done", hard_reject: false },
      { step: "byzantium", status: "done", trust_score: 684, decision: "REVIEW" },
    ],
  }),
  preparedScenario({
    id: "PREPARED-SLATE-03",
    title: "Conflicting evidence path",
    path: "Escalate path",
    summary: "A synthetic integrity conflict that demonstrates a safe human escalation.",
    analysis: {
      video_analysis: { collision: false, severity: "uncertain", timestamp: "00:00:09", summary: "Synthetic footage sample contains inconsistent impact cues.", fault: "undetermined", vehicle_count: 1, conditions: "uncertain", audio_evidence: "Synthetic sample: audio and motion signals do not align.", damage_description: "Synthetic sample: no reliable damage observation.", camera_pov: "first_person", point_of_impact: "undetermined", plate_detected: "not_visible", source: PREPARED_SOURCE },
      identity_result: { verified: false, identity_score: 38, source: PREPARED_SOURCE },
      myinfo_result: { verified: false, full_name: "Synthetic Driver Slate", vehicle_plate: "DEMO-SLATE", vehicle_make: "Illustrative", vehicle_model: "Vehicle", licence_valid: true, licence_class: "Synthetic", demerit_points: 0, licence_suspended: false, vehicle_ownership_confirmed: false, myinfo_score: 38, source: PREPARED_SOURCE, triggered_by: "prepared walkthrough" },
      nosana_analysis: { job_id: "PREPARED-SLATE-COMPUTE", clip_verdict: "COLLISION_UNCERTAIN", collision_signal_strength: 24, integrity_score: 31, editing_artifacts_detected: true, corroboration: "WEAK", scene_labels: ["synthetic_signal_conflict", "integrity_review"], frame_count_analyzed: 64 },
      kimi_result: { decision: "REJECT", reason: "Prepared escalation branch: conflicting synthetic evidence requires a licensed human reviewer. No real claim is denied here.", confidence: 0.79, source: PREPARED_SOURCE },
      trust_score_result: { trust_score: 216, risk_level: "HIGH", decision: "REJECT", reason: "Prepared escalation path only. The conflicting signals demonstrate a stop-and-review control, not a coverage denial or legal finding.", breakdown: { synthetic_identity_conflict: -180, synthetic_integrity_conflict: -260, synthetic_evidence_gap: -144 } },
      payout_amount: 0,
    },
    receipt: { claimant_name: "Synthetic Driver Slate", policy_number: "DEMO-SLATE", identity_status: "PREPARED CONFLICT", video_status: "PREPARED SYNTHETIC CONFLICT", trust_score: 216, risk_level: "HIGH", decision: "REJECT", reason: "Prepared escalation receipt only. It directs a fictional case to human review and does not deny a real claim or determine coverage.", payout_amount: 0, timestamp: "2026-06-01T09:10:00.000Z", receipt_number: "PREPARED-SLATE-03", plate_detected: "not_visible" },
    events: [
      { step: "nosana", status: "done", job_id: "PREPARED-SLATE-COMPUTE", clip_verdict: "COLLISION_UNCERTAIN", collision_signal_strength: 24, integrity_score: 31, editing_artifacts_detected: true, corroboration: "WEAK" },
      { step: "videodb", status: "done", collision: false, severity: "uncertain", timestamp: "00:00:09" },
      { step: "terminal3", status: "done", verified: false, identity_score: 38 },
      { step: "myinfo", status: "done", verified: false, full_name: "Synthetic Driver Slate", vehicle_plate: "DEMO-SLATE", demerit_points: 0, licence_suspended: false },
      { step: "kimi", status: "done", decision: "REJECT", reason: "Prepared escalation path" },
      { step: "daytona", status: "done", hard_reject: true },
      { step: "byzantium", status: "done", trust_score: 216, decision: "REJECT" },
    ],
  }),
];

export const PREPARED_CLAIM_ID = PREPARED_SCENARIOS[1].id;
export const preparedClaim = PREPARED_SCENARIOS[1];
export const preparedPipelineEvents = preparedClaim.pipeline_events;

export function getPreparedScenario(id) {
  return PREPARED_SCENARIOS.find((scenario) => scenario.id === id) || null;
}

export function isLoopbackHostname(hostname) {
  return ["localhost", "127.0.0.1", "::1", "[::1]"].includes(String(hostname).toLowerCase());
}

export function isPreparedShowcase() {
  if (typeof window === "undefined") return true;

  const hostname = window.location.hostname.toLowerCase();
  const isLocalHost = isLoopbackHostname(hostname);
  const liveOperatorOptIn = typeof import.meta.env !== "undefined" && import.meta.env.VITE_LIVE_OPERATOR === "true";

  // Public deployments fail closed into the synthetic showcase. The live
  // upload/PII workflow is available only through an explicit local opt-in.
  return !(isLocalHost && liveOperatorOptIn);
}
