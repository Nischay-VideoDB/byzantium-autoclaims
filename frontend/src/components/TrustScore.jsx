export default function TrustScore({ score, riskLevel }) {
  const pct = Math.min(100, (score / 1000) * 100);

  const color =
    riskLevel === "LOW"
      ? { bar: "bg-green-500", text: "text-green-400", ring: "ring-green-500/20" }
      : riskLevel === "MEDIUM"
      ? { bar: "bg-yellow-500", text: "text-yellow-400", ring: "ring-yellow-500/20" }
      : { bar: "bg-red-500", text: "text-red-400", ring: "ring-red-500/20" };

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-2xl p-6 ring-2 ${color.ring}`}>
      <div className="flex items-end justify-between mb-3">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Trust Score</p>
          <p className={`text-5xl font-black ${color.text}`}>{score}</p>
          <p className="text-gray-500 text-sm">/ 1000</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Risk Level</p>
          <span
            className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${
              riskLevel === "LOW"
                ? "bg-green-500/10 text-green-400 border border-green-500/30"
                : riskLevel === "MEDIUM"
                ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30"
                : "bg-red-500/10 text-red-400 border border-red-500/30"
            }`}
          >
            {riskLevel}
          </span>
        </div>
      </div>

      <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-1000 ease-out ${color.bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="flex justify-between mt-1.5 text-xs text-gray-600">
        <span>0</span>
        <span>REJECT &lt; 400 &lt; REVIEW &lt; 700 &lt; APPROVE</span>
        <span>1000</span>
      </div>
    </div>
  );
}
