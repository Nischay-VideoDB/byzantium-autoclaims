export default function DecisionBadge({ decision, size = "lg" }) {
  const cfg = {
    APPROVE: {
      bg: "bg-green-500/10",
      border: "border-green-500/40",
      text: "text-green-400",
      glow: "shadow-[0_0_30px_rgba(34,197,94,0.2)]",
      icon: "✓",
      label: "APPROVED",
    },
    REJECT: {
      bg: "bg-red-500/10",
      border: "border-red-500/40",
      text: "text-red-400",
      glow: "shadow-[0_0_30px_rgba(239,68,68,0.2)]",
      icon: "✕",
      label: "REJECTED",
    },
    REVIEW: {
      bg: "bg-yellow-500/10",
      border: "border-yellow-500/40",
      text: "text-yellow-400",
      glow: "shadow-[0_0_30px_rgba(234,179,8,0.2)]",
      icon: "⚠",
      label: "UNDER REVIEW",
    },
  };

  const c = cfg[decision] || cfg.REVIEW;

  if (size === "lg") {
    return (
      <div
        className={`${c.bg} border-2 ${c.border} ${c.glow} rounded-2xl p-8 text-center`}
      >
        <div className={`text-6xl font-black ${c.text} mb-2`}>{c.icon}</div>
        <div className={`text-3xl font-black ${c.text} tracking-widest`}>{c.label}</div>
      </div>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold ${c.bg} border ${c.border} ${c.text}`}
    >
      {c.icon} {c.label}
    </span>
  );
}
