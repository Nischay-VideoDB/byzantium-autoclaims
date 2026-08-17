export const PREPARED_CLAIM_ID = "DEMO-CLM-2026-01";

export const preparedClaim = {
  analysis: {
    claim_id: PREPARED_CLAIM_ID,
    status: "complete",
    video_analysis: {
      collision: true,
      severity: "medium",
      timestamp: "00:00:14",
      summary: "Prepared synthetic dashcam scenario: an example vehicle is stationary at a red light and is struck from behind.",
      fault: "other_party",
      vehicle_count: 2,
      conditions: "clear_daylight",
      single_vehicle: false,
      audio_evidence: "Prepared sample: an impact sound followed by a horn.",
      damage_description: "Prepared sample: rear bumper damage is visible.",
      camera_pov: "first_person",
      point_of_impact: "rear",
      plate_detected: "not_visible",
      source: "prepared-synthetic",
    },
    identity_result: {
      verified: true,
      identity_score: 91,
      source: "prepared-synthetic",
    },
    myinfo_result: {
      verified: true,
      full_name: "Synthetic Driver",
      vehicle_plate: "DEMO-ONLY",
      vehicle_make: "Example",
      vehicle_model: "Vehicle",
      licence_valid: true,
      licence_class: "Example",
      demerit_points: 0,
      licence_suspended: false,
      vehicle_ownership_confirmed: false,
      myinfo_score: 91,
      source: "prepared-synthetic",
      triggered_by: "prepared walkthrough",
    },
    nosana_analysis: {
      job_id: "PREPARED-NOSANA-01",
      clip_verdict: "COLLISION_CONFIRMED",
      collision_signal_strength: 78,
      integrity_score: 86,
      editing_artifacts_detected: false,
      corroboration: "STRONG",
      scene_labels: ["vehicle_collision", "rear_impact"],
      frame_count_analyzed: 120,
    },
    kimi_result: {
      decision: "REVIEW",
      reason: "Prepared example evidence supports a rear-end collision, but a qualified human reviewer must make any real insurance determination.",
      confidence: 0.84,
      source: "prepared-synthetic",
    },
    trust_score_result: {
      trust_score: 684,
      risk_level: "MEDIUM",
      decision: "REVIEW",
      reason: "Prepared walkthrough outcome: the example evidence is coherent, but this public demo cannot verify a person, policy, footage, or payout. A real claim requires qualified human review.",
      breakdown: {
        prepared_identity_signal: 300,
        prepared_collision_signal: 300,
        prepared_severity_signal: 150,
        human_review_required: -66,
      },
    },
    payout_amount: 0,
  },
  receipt: {
    claim_id: PREPARED_CLAIM_ID,
    claimant_name: "Synthetic Driver",
    policy_number: "DEMO-ONLY",
    identity_status: "PREPARED SAMPLE",
    video_status: "PREPARED SYNTHETIC EVIDENCE",
    trust_score: 684,
    risk_level: "MEDIUM",
    decision: "REVIEW",
    reason: "Prepared walkthrough only. No claim was submitted, no evidence was verified, and no coverage or payout determination was made.",
    payout_amount: 0,
    timestamp: "2026-06-01T09:00:00.000Z",
    receipt_number: "DEMO-AUDIT-01",
    plate_detected: "not_visible",
  },
};

export const preparedPipelineEvents = [
  {
    step: "nosana",
    status: "done",
    job_id: preparedClaim.analysis.nosana_analysis.job_id,
    ...preparedClaim.analysis.nosana_analysis,
  },
  {
    step: "videodb",
    status: "done",
    ...preparedClaim.analysis.video_analysis,
  },
  {
    step: "terminal3",
    status: "done",
    ...preparedClaim.analysis.identity_result,
  },
  {
    step: "myinfo",
    status: "done",
    ...preparedClaim.analysis.myinfo_result,
  },
  {
    step: "kimi",
    status: "done",
    ...preparedClaim.analysis.kimi_result,
  },
  {
    step: "daytona",
    status: "done",
    hard_reject: false,
  },
  {
    step: "byzantium",
    status: "done",
    ...preparedClaim.analysis.trust_score_result,
  },
];

export function isPreparedShowcase() {
  return typeof window !== "undefined" && window.location.hostname.endsWith(".vercel.app");
}
