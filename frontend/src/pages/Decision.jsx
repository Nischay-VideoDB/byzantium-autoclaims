import TrustScore from "../components/TrustScore";
import DecisionBadge from "../components/DecisionBadge";

function CrashFrame({ frameUrl, clipUrl, plateDetected }) {
  // Show the crash frame screenshot — prefer still frame_url, fall back to clip
  const src = frameUrl || clipUrl;
  if (!src) return null;

  const isVideo = src.includes("m3u8") || src.includes(".mp4") || src.includes("stream");

  return (
    <div className="bg-black border border-red-500/30 rounded-xl overflow-hidden mb-5">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-800">
        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        <span className="text-xs text-red-400 font-semibold uppercase tracking-widest">Crash Frame — VideoDB</span>
        {plateDetected && plateDetected !== "not_visible" && (
          <span className="ml-auto text-xs font-mono bg-gray-800 text-gray-300 px-2 py-0.5 rounded">
            🚗 {plateDetected}
          </span>
        )}
      </div>
      {isVideo ? (
        <video
          src={src}
          muted
          autoPlay={false}
          controls
          playsInline
          className="w-full max-h-64 object-contain bg-black"
          onLoadedMetadata={(e) => { e.target.currentTime = 0; }}
        />
      ) : (
        <img src={src} alt="Crash frame" className="w-full max-h-64 object-contain bg-black" />
      )}
    </div>
  );
}

function EvidenceCard({ icon, title, value, verified }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{icon}</span>
        <span className="text-xs text-gray-500 uppercase tracking-widest">{title}</span>
        <span
          className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full ${
            verified
              ? "text-green-400 bg-green-500/10"
              : "text-red-400 bg-red-500/10"
          }`}
        >
          {verified ? "✓ Verified" : "✕ Failed"}
        </span>
      </div>
      <p className="text-gray-300 text-sm">{value}</p>
    </div>
  );
}

function ScoreBreakdown({ breakdown }) {
  if (!breakdown) return null;
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">Score Breakdown</p>
      <div className="space-y-2">
        {Object.entries(breakdown).map(([key, val]) => {
          const isPos = val > 0;
          return (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-gray-400 capitalize">{key.replace(/_/g, " ")}</span>
              <span className={isPos ? "text-green-400 font-bold" : "text-red-400 font-bold"}>
                {isPos ? "+" : ""}{val}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MyInfoCard({ myinfo }) {
  if (!myinfo || !myinfo.verified) return null;
  return (
    <div className="bg-gray-900 border border-purple-500/20 rounded-xl p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">🇸🇬</span>
        <span className="text-xs text-gray-500 uppercase tracking-widest">SingPass MyInfo</span>
        <span className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full ${
          myinfo.licence_suspended ? "text-red-400 bg-red-500/10" : "text-purple-400 bg-purple-500/10"
        }`}>
          {myinfo.licence_suspended ? "✕ SUSPENDED" : "✓ Gov Verified"}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
        <span className="text-gray-500">Name</span>
        <span className="text-gray-300">{myinfo.full_name}</span>
        <span className="text-gray-500">Vehicle</span>
        <span className="text-gray-300">{myinfo.vehicle_make} {myinfo.vehicle_model} · {myinfo.vehicle_plate}</span>
        <span className="text-gray-500">Ownership</span>
        <span className={myinfo.vehicle_ownership_confirmed ? "text-green-400" : "text-gray-400"}>
          {myinfo.vehicle_ownership_confirmed ? "Confirmed in footage" : "Not confirmed"}
        </span>
        <span className="text-gray-500">Licence</span>
        <span className={myinfo.licence_valid && !myinfo.licence_suspended ? "text-green-400" : "text-red-400"}>
          {myinfo.licence_suspended ? "SUSPENDED" : myinfo.licence_valid ? `Valid · Class ${myinfo.licence_class}` : "Invalid"}
        </span>
        <span className="text-gray-500">Demerit pts</span>
        <span className={myinfo.demerit_points >= 12 ? "text-red-400" : myinfo.demerit_points >= 6 ? "text-yellow-400" : "text-gray-300"}>
          {myinfo.demerit_points}/24
        </span>
        <span className="text-gray-500">MyInfo score</span>
        <span className="text-purple-300 font-bold">{myinfo.myinfo_score}/100</span>
      </div>
    </div>
  );
}

function NosanaCard({ nosana }) {
  if (!nosana || !nosana.clip_verdict) return null;
  const verdictColor =
    nosana.clip_verdict === "COLLISION_CONFIRMED" ? "text-green-400 bg-green-500/10" :
    nosana.clip_verdict === "COLLISION_POSSIBLE"  ? "text-yellow-400 bg-yellow-500/10" :
                                                    "text-red-400 bg-red-500/10";
  const corrColor =
    nosana.corroboration === "STRONG"   ? "text-green-400" :
    nosana.corroboration === "MODERATE" ? "text-yellow-400" : "text-red-400";

  return (
    <div className="bg-gray-900 border border-orange-500/20 rounded-xl p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">⚡</span>
        <span className="text-xs text-gray-500 uppercase tracking-widest">Nosana GPU · CLIP-ViT-B/32</span>
        <span className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full ${verdictColor}`}>
          {nosana.clip_verdict.replace(/_/g, " ")}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
        <span className="text-gray-500">Signal strength</span>
        <span className="text-gray-300">{nosana.collision_signal_strength}/100</span>
        <span className="text-gray-500">Integrity score</span>
        <span className={nosana.integrity_score >= 70 ? "text-green-400" : "text-yellow-400"}>
          {nosana.integrity_score}/100
        </span>
        <span className="text-gray-500">Editing artifacts</span>
        <span className={nosana.editing_artifacts_detected ? "text-red-400" : "text-green-400"}>
          {nosana.editing_artifacts_detected ? "Detected" : "None detected"}
        </span>
        <span className="text-gray-500">Corroboration</span>
        <span className={`font-bold ${corrColor}`}>{nosana.corroboration}</span>
        <span className="text-gray-500">Scene labels</span>
        <span className="text-gray-300 text-xs">{(nosana.scene_labels || []).join(", ")}</span>
        <span className="text-gray-500">Frames analyzed</span>
        <span className="text-gray-300">{nosana.frame_count_analyzed?.toLocaleString() || "—"}</span>
      </div>
    </div>
  );
}

export default function Decision({ data, onViewReceipt }) {
  if (!data) return null;

  const { video_analysis, identity_result, myinfo_result, nosana_analysis, kimi_result, trust_score_result, payout_amount } = data;

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-1">Claim Decision</h2>
        <p className="text-gray-400 text-sm">
          Byzantium has evaluated all evidence and made a final determination.
        </p>
      </div>

      <CrashFrame
        frameUrl={video_analysis?.frame_url}
        clipUrl={video_analysis?.clip_url}
        plateDetected={video_analysis?.plate_detected}
      />

      {/* Trust score + decision side by side */}
      <div className="grid grid-cols-1 gap-4 mb-6">
        <TrustScore
          score={trust_score_result.trust_score}
          riskLevel={trust_score_result.risk_level}
        />
        <DecisionBadge decision={trust_score_result.decision} size="lg" />
      </div>

      {/* Reason */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">AI Reasoning</p>
        <p className="text-gray-300 text-sm leading-relaxed">{trust_score_result.reason}</p>
        <div className="mt-3 pt-3 border-t border-gray-800 flex items-center gap-2">
          <span className="text-xs text-gray-500">Kimi AI:</span>
          <span className="text-xs text-gray-400 italic">
            "{kimi_result.reason}"
          </span>
          <span className="ml-auto text-xs text-gray-600">
            {(kimi_result.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>
      </div>

      {/* Evidence cards */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <EvidenceCard
          icon="🎬"
          title="Video Evidence"
          value={video_analysis.collision ? `${video_analysis.severity.toUpperCase()} collision — ${video_analysis.fault?.replace(/_/g, " ")}` : "No collision detected"}
          verified={video_analysis.collision}
        />
        <EvidenceCard
          icon="🛡️"
          title="Identity"
          value={`Score: ${identity_result.identity_score}/100 via ${identity_result.source}`}
          verified={identity_result.verified}
        />
      </div>

      <NosanaCard nosana={nosana_analysis} />
      <MyInfoCard myinfo={myinfo_result} />

      <ScoreBreakdown breakdown={trust_score_result.breakdown} />

      {/* Payout simulation */}
      {trust_score_result.decision === "APPROVE" && (
        <div className="mt-4 bg-green-500/5 border border-green-500/20 rounded-xl p-5 text-center">
          <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Payout Authorized</p>
          <p className="text-4xl font-black text-green-400">
            💰 ${payout_amount.toLocaleString()}
          </p>
          <p className="text-gray-500 text-xs mt-1">Simulated — no real funds transferred</p>
        </div>
      )}

      {trust_score_result.decision === "REJECT" && (
        <div className="mt-4 bg-red-500/5 border border-red-500/20 rounded-xl p-5 text-center">
          <p className="text-4xl font-black text-red-400">💸 $0.00</p>
          <p className="text-gray-500 text-xs mt-1">Claim does not meet approval criteria</p>
        </div>
      )}

      {trust_score_result.decision === "REVIEW" && (
        <div className="mt-4 bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-5 text-center">
          <p className="text-yellow-400 font-bold">⏳ Pending Manual Review</p>
          <p className="text-gray-500 text-xs mt-1">A claims agent will review this within 24 hours</p>
        </div>
      )}

      <button
        onClick={onViewReceipt}
        className="w-full mt-6 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3.5 rounded-xl transition-all"
      >
        View Liability Receipt →
      </button>
    </div>
  );
}
