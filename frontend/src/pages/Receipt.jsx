import { useState, useEffect } from "react";
import { getReceipt } from "../api";
import DecisionBadge from "../components/DecisionBadge";

function ReceiptRow({ label, value, highlight }) {
  return (
    <div className={`flex items-start justify-between py-3 border-b border-gray-800 last:border-0 ${highlight ? "bg-gray-900/50 -mx-5 px-5 rounded" : ""}`}>
      <span className="text-xs text-gray-500 uppercase tracking-widest w-36 flex-shrink-0 pt-0.5">{label}</span>
      <span className={`text-sm text-right ${highlight ? "text-white font-bold" : "text-gray-300"}`}>{value}</span>
    </div>
  );
}

export default function Receipt({ claimId, onReset, preparedReceipt = null }) {
  const [receipt, setReceipt] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (preparedReceipt) {
      setReceipt(preparedReceipt);
      return;
    }

    getReceipt(claimId)
      .then(setReceipt)
      .catch((err) => setError(err.message));
  }, [claimId, preparedReceipt]);

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-red-400 text-sm">
        <p className="font-semibold mb-1">Could not load receipt</p>
        <p>{error}</p>
      </div>
    );
  }

  if (!receipt) {
    return (
      <div className="text-center py-16 text-gray-500">
        <svg className="animate-spin w-8 h-8 mx-auto mb-3" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
        Loading receipt...
      </div>
    );
  }

  const ts = new Date(receipt.timestamp).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  const src = receipt.frame_url || receipt.clip_url;
  const isVideo = src && (src.includes("m3u8") || src.includes(".mp4") || src.includes("stream"));

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-1">{preparedReceipt ? "Prepared Audit Receipt" : "Liability Receipt"}</h2>
        <p className="text-gray-400 text-sm">
          {preparedReceipt
            ? "A non-binding synthetic audit record for the public product walkthrough."
            : "Official record of the Byzantium claims decision."}
        </p>
      </div>

      {/* Crash frame evidence */}
      {src && (
        <div className="bg-black border border-red-500/30 rounded-xl overflow-hidden mb-5">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-800">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-xs text-red-400 font-semibold uppercase tracking-widest">Crash Frame Evidence</span>
            {receipt.plate_detected && receipt.plate_detected !== "not_visible" && (
              <span className="ml-auto text-xs font-mono bg-gray-800 text-gray-300 px-2 py-0.5 rounded">
                🚗 {receipt.plate_detected}
              </span>
            )}
          </div>
          {isVideo ? (
            <video
              src={src}
              muted
              controls
              playsInline
              className="w-full max-h-56 object-contain bg-black"
              onLoadedMetadata={(e) => { e.target.currentTime = 0; }}
            />
          ) : (
            <img src={src} alt="Crash frame" className="w-full max-h-56 object-contain bg-black" />
          )}
        </div>
      )}

      {/* Receipt card */}
      <div className="bg-gray-900 border border-gray-700 rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gray-800/60 px-6 py-5 border-b border-gray-700">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center text-xs font-bold text-white">TG</div>
                <span className="text-sm font-bold text-white">Byzantium AutoClaims</span>
              </div>
              <p className="text-xs text-gray-500">Autonomous Insurance Claims System</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500 mb-0.5">{preparedReceipt ? "Prepared record" : "Receipt"}</p>
              <p className="font-mono font-bold text-white text-sm">{receipt.receipt_number}</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-2">
          <ReceiptRow label="Claim ID" value={receipt.claim_id} />
          <ReceiptRow label="Claimant" value={receipt.claimant_name} />
          <ReceiptRow label="Policy" value={receipt.policy_number} />
          <ReceiptRow label="Date &amp; Time" value={ts} />
          <ReceiptRow label="Identity" value={receipt.identity_status} />
          <ReceiptRow label="Video Evidence" value={receipt.video_status} />
          {receipt.plate_detected && receipt.plate_detected !== "not_visible" && (
            <ReceiptRow label="Plate Detected" value={receipt.plate_detected} />
          )}
          <ReceiptRow label="Trust Score" value={`${receipt.trust_score} / 1000`} />
          <ReceiptRow label="Risk Level" value={receipt.risk_level} />
        </div>

        {/* Decision highlight */}
        <div className="px-6 py-5 border-t border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs text-gray-500 uppercase tracking-widest">Decision</span>
            <DecisionBadge decision={receipt.decision} size="sm" prepared={Boolean(preparedReceipt)} />
          </div>
          <p className="text-sm text-gray-300 leading-relaxed">{receipt.reason}</p>
        </div>

        {/* Payout */}
        <div className={`px-6 py-5 border-t ${
          receipt.decision === "APPROVE"
            ? "border-green-500/20 bg-green-500/5"
            : receipt.decision === "REJECT"
            ? "border-red-500/20 bg-red-500/5"
            : "border-yellow-500/20 bg-yellow-500/5"
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">
                {preparedReceipt ? "Illustrative amount" : receipt.decision === "APPROVE" ? "Authorized Payout" : "Payout"}
              </p>
              <p className={`text-3xl font-black ${
                receipt.decision === "APPROVE" ? "text-green-400" : "text-gray-500"
              }`}>
                {preparedReceipt
                  ? receipt.decision === "APPROVE" ? `$${receipt.payout_amount.toLocaleString()}` : "Not assessed"
                  : receipt.decision === "APPROVE" ? `$${receipt.payout_amount.toLocaleString()}` : receipt.decision === "REVIEW" ? "Pending" : "$0.00"}
              </p>
            </div>
            {receipt.decision === "APPROVE" && (
              <div className="text-4xl">💰</div>
            )}
          </div>
          {receipt.decision !== "REVIEW" && (
            <p className="text-xs text-gray-600 mt-2">{preparedReceipt ? "Prepared amount only - no authorization, guarantee, or funds transfer." : "Simulated payout — no real funds transferred"}</p>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800 bg-gray-900/30">
          <p className="text-xs text-gray-600 text-center">
            {preparedReceipt
              ? "Prepared synthetic walkthrough - not a claim, policy record, evidence verification, or payout authorization."
              : "This receipt was generated automatically by Byzantium AutoClaims. Powered by VideoDB · Terminal 3 · Kimi AI · Daytona · Nosana."}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 mt-6">
        <button
          onClick={() => window.print()}
          className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold py-3 rounded-xl transition-all text-sm"
        >
          Print Receipt
        </button>
        <button
          onClick={onReset}
          className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all text-sm"
        >
          {preparedReceipt ? "Choose another prepared example" : "File Another Claim"}
        </button>
      </div>
    </div>
  );
}
