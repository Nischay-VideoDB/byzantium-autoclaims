import { useState, useEffect, useRef } from "react";
import { streamClaim } from "../api";

const PIPELINE_STEPS = [
  { key: "nosana",    label: "Nosana GPU Compute",    icon: "⚡", desc: "Submitting video processing job to decentralized compute..." },
  { key: "videodb",   label: "VideoDB Analysis",       icon: "🎬", desc: "Indexing scenes and spoken words from dashcam footage..." },
  { key: "terminal3", label: "Terminal 3 Identity",    icon: "🛡️", desc: "Verifying claimant identity via TEE attestation..." },
  { key: "myinfo",    label: "SingPass MyInfo",        icon: "🇸🇬", desc: "Fetching government-verified vehicle & licence data..." },
  { key: "kimi",      label: "Kimi AI Evaluation",     icon: "🤖", desc: "Cross-referencing evidence against policy document..." },
  { key: "daytona",   label: "Daytona ClaimAgent",     icon: "🔒", desc: "Enforcing hard policy rules in secure sandbox..." },
  { key: "byzantium", label: "Byzantium Decision",     icon: "⚖️", desc: "Calculating final trust score and decision..." },
];

function StepRow({ step, state, result, prepared = false }) {
  const preparedSubtitle = {
    nosana: result?.clip_verdict ? `Prepared: ${result.clip_verdict.replace(/_/g, " ").toLowerCase()} · integrity ${result.integrity_score}/100` : null,
    videodb: result ? `Prepared: ${result.collision ? `${result.severity} collision cue @ ${result.timestamp}` : "conflicting collision cues"}` : null,
    terminal3: result ? `Prepared: ${result.verified ? "identity signal aligned" : "identity signal conflicted"} · ${result.identity_score}/100` : null,
    myinfo: result ? `Prepared: ${result.verified ? "policy signal aligned" : "policy signal conflicted"} · ${result.vehicle_plate}` : null,
    kimi: result ? `Prepared: ${result.decision.toLowerCase()} path selected` : null,
    daytona: result ? `Prepared: ${result.hard_reject ? "stop-and-escalate control" : "review controls applied"}` : null,
    byzantium: result ? `Prepared: score ${result.trust_score}/1000 · ${result.decision.toLowerCase()} path` : null,
  }[step.key];
  const subtitle = prepared && result
    ? `${preparedSubtitle || "Prepared synthetic signal"} - no provider was contacted.`
    : {
    nosana:    result ? (
      result.clip_verdict
        ? `${result.clip_verdict} · signal ${result.collision_signal_strength}/100 · integrity ${result.integrity_score}/100 · corroboration: ${result.corroboration}`
        : `Job ${result.job_id || "submitted"} — GPU allocated`
    ) : step.desc,
    videodb:   result ? `${result.collision ? `${result.severity?.toUpperCase()} collision @ ${result.timestamp}` : "No collision detected"}` : step.desc,
    terminal3: result ? `${result.verified ? "✓ Verified" : "✗ Failed"} — T3 score: ${result.identity_score}/100` : step.desc,
    myinfo:    state === "skipped" ? `Skipped — ${result?.reason || "video evidence sufficient"}` :
               result ? `${result.verified ? `✓ ${result.full_name} · ${result.vehicle_plate}` : "✗ NRIC not matched"} · ${result.demerit_points} demerit pts${result.licence_suspended ? " · SUSPENDED" : ""}` : step.desc,
    kimi:      result ? `${result.decision} — ${result.reason?.slice(0, 70)}...` : step.desc,
    daytona:   result ? `ClaimAgent executed${result.hard_reject ? " — hard reject triggered" : " — scoring applied"}` : step.desc,
    byzantium: result ? `Trust score: ${result.trust_score}/1000 — ${result.decision}` : step.desc,
  }[step.key] || step.desc;

  return (
    <div className={`flex items-start gap-4 p-4 rounded-xl border transition-all duration-500 ${
      state === "done"    ? "border-green-500/20 bg-green-500/5"  :
      state === "running" ? "border-blue-500/30 bg-blue-500/5"   :
      state === "skipped" ? "border-gray-700/40 bg-gray-900/30"  :
                            "border-gray-800 bg-gray-900/50 opacity-40"
    }`}>
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0 ${
        state === "done"    ? "bg-green-500/20"  :
        state === "running" ? "bg-blue-500/20"   :
        state === "skipped" ? "bg-gray-700/40"   : "bg-gray-800"
      }`}>
        {state === "done" ? (
          <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
        ) : state === "running" ? (
          <svg className="w-5 h-5 text-blue-400 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
        ) : state === "skipped" ? (
          <span className="text-gray-500 text-base">—</span>
        ) : <span>{step.icon}</span>}
      </div>

      <div className="flex-1 min-w-0">
        <p className={`font-semibold text-sm ${
          state === "done"    ? "text-green-300" :
          state === "running" ? "text-blue-300"  :
          state === "skipped" ? "text-gray-600"  : "text-gray-500"
        }`}>{step.label}</p>
        <p className="text-xs text-gray-400 mt-0.5 truncate">{subtitle}</p>
      </div>

      {state === "running" && (
        <span className="text-xs text-blue-400 animate-pulse flex-shrink-0">
          {prepared ? "Prepared step" : "Live"}
        </span>
      )}
    </div>
  );
}

function CollisionClip({ clipUrl }) {
  if (!clipUrl) return null;
  return (
    <div className="mt-5 bg-gray-900 border border-green-500/20 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-800">
        <span className="text-xs text-green-400 font-semibold uppercase tracking-widest">
          🎬 Collision Evidence Clip
        </span>
        <span className="ml-auto text-xs text-gray-500">Generated by VideoDB</span>
      </div>
      <video
        src={clipUrl}
        controls
        autoPlay
        muted
        className="w-full max-h-56 object-cover bg-black"
      />
    </div>
  );
}

export default function Analysis({ claimId, onAnalyzed, prepared = null }) {
  const [stepStates, setStepStates] = useState({});
  const [stepResults, setStepResults] = useState({});
  const [clipUrl, setClipUrl] = useState("");
  const [error, setError] = useState(null);
  const cleanupRef = useRef(null);

  useEffect(() => {
    if (prepared) {
      let cancelled = false;
      const timers = [];

      prepared.pipeline_events.forEach((event, index) => {
        timers.push(setTimeout(() => {
          if (!cancelled) {
            setStepStates((previous) => ({ ...previous, [event.step]: "running" }));
          }
        }, index * 260));
        timers.push(setTimeout(() => {
          if (!cancelled) {
            setStepStates((previous) => ({ ...previous, [event.step]: event.status }));
            setStepResults((previous) => ({ ...previous, [event.step]: event }));
          }
        }, index * 260 + 180));
      });

      timers.push(setTimeout(() => {
        if (!cancelled) onAnalyzed(prepared.analysis);
      }, prepared.pipeline_events.length * 260 + 260));

      return () => {
        cancelled = true;
        timers.forEach(clearTimeout);
      };
    }

    cleanupRef.current = streamClaim(
      claimId,
      // onStep
      (data) => {
        const { step, status } = data;
        setStepStates((prev) => ({ ...prev, [step]: status }));

        if (status === "done" || status === "skipped") {
          setStepResults((prev) => ({ ...prev, [step]: data }));
          if (step === "videodb" && data.clip_url) {
            setClipUrl(data.clip_url);
          }
        }
      },
      // onComplete
      (data) => {
        // Mark any remaining pending/running as done; preserve skipped
        setStepStates((prev) =>
          Object.fromEntries(
            PIPELINE_STEPS.map((s) => [s.key, prev[s.key] === "skipped" ? "skipped" : "done"])
          )
        );
        setTimeout(() => onAnalyzed(data), 600);
      },
      // onError
      (err) => setError(err.message)
    );

    return () => cleanupRef.current?.();
  }, [claimId, onAnalyzed, prepared]);

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-2xl font-bold text-white">{prepared ? "Prepared Evidence Walkthrough" : "Analyzing Claim"}</h2>
          <span className="text-xs font-mono text-gray-500 bg-gray-900 border border-gray-800 px-2.5 py-1 rounded">
            {prepared ? prepared.id : claimId}
          </span>
        </div>
        <p className="text-gray-400 text-sm">
          {prepared
            ? "Prepared synthetic stages - no video, identity, policy, or provider is contacted."
            : "Live pipeline — each step updates as it completes."}
        </p>
      </div>

      <div className="space-y-3">
        {PIPELINE_STEPS.map((step) => (
          <StepRow
            key={step.key}
            step={step}
            state={stepStates[step.key] || "pending"}
            result={stepResults[step.key]}
            prepared={Boolean(prepared)}
          />
        ))}
      </div>

      <CollisionClip clipUrl={clipUrl} />

      {error && (
        <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-xl px-5 py-4 text-red-400">
          <p className="font-semibold text-sm mb-1">Analysis failed</p>
          <p className="text-xs">{error}</p>
          <p className="text-xs mt-2 text-gray-500">
            Make sure the backend is running: <code className="text-gray-400">uvicorn main:app --reload</code>
          </p>
        </div>
      )}
    </div>
  );
}
