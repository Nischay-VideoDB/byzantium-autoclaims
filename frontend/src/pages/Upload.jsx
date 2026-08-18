import { useState, useRef, useCallback } from "react";
import { uploadClaim, lookupPolicy } from "../api";
import { PREPARED_SCENARIOS } from "../preparedDemo";

export default function Upload({ onUploaded, onStartPreparedDemo, publicShowcase = false }) {
  const [file, setFile] = useState(null);
  const [form, setForm] = useState({
    claimantName: "",
    claimantId: "",
    nric: "",
    vehiclePlate: "",
  });
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Policy lookup state
  const [policyLookup, setPolicyLookup] = useState(null); // null | {loading} | {match, policy_name, ...}
  const lookupDebounceRef = useRef(null);

  const inputRef = useRef();

  function handleFile(f) {
    if (f && f.type.startsWith("video/")) {
      setFile(f);
      setError(null);
    } else {
      setError("Please upload a video file (.mp4, .mov, .avi)");
    }
  }

  function fillSyntheticPersona() {
    const next = { claimantName: "Jane Smith", claimantId: "DEMO-LICENCE", nric: "S9812381D", vehiclePlate: "SLD9775A" };
    setForm(next);
    triggerPolicyLookup(next.claimantName, next.vehiclePlate);
  }

  async function loadSampleFootage() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4");
      if (!response.ok) throw new Error("sample download failed");
      const blob = await response.blob();
      setFile(new File([blob], "synthetic-demo-footage.mp4", { type: "video/mp4" }));
      fillSyntheticPersona();
    } catch {
      setError("The sample footage could not be loaded. Upload an MP4 under 20 MB instead.");
    } finally {
      setLoading(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }

  // Debounced policy lookup when name + plate are both filled
  const triggerPolicyLookup = useCallback((name, plate) => {
    clearTimeout(lookupDebounceRef.current);
    if (!name.trim() || !plate.trim() || plate.length < 5) {
      setPolicyLookup(null);
      return;
    }
    setPolicyLookup({ loading: true });
    lookupDebounceRef.current = setTimeout(async () => {
      try {
        const result = await lookupPolicy(name.trim(), plate.trim().toUpperCase());
        setPolicyLookup(result);
      } catch (err) {
        // 404 = no policy found
        setPolicyLookup({ notFound: true, plate: plate.trim().toUpperCase() });
      }
    }, 600);
  }, []);

  function handleFieldChange(field, value) {
    const next = { ...form, [field]: value };
    setForm(next);
    if (field === "claimantName" || field === "vehiclePlate") {
      triggerPolicyLookup(
        field === "claimantName" ? value : next.claimantName,
        field === "vehiclePlate" ? value : next.vehiclePlate,
      );
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return setError("Please upload a dashcam video.");
    if (!form.claimantName.trim()) return setError("Claimant name is required.");
    if (!form.vehiclePlate.trim()) return setError("Vehicle plate is required.");

    // Block submission if policy found but name doesn't match
    if (policyLookup && !policyLookup.loading && !policyLookup.notFound) {
      if (!policyLookup.match) {
        return setError(
          `Policy verification failed: name or plate does not match policy records ` +
          `(policy insured: ${policyLookup.insured_name || "unknown"}, plate: ${policyLookup.vehicle_plate || "unknown"}).`
        );
      }
    }

    setLoading(true);
    setError(null);
    try {
      const uploadRes = await uploadClaim({
        video: file,
        claimantName: form.claimantName,
        claimantId: form.claimantId,
        nric: form.nric,
        vehiclePlate: form.vehiclePlate.toUpperCase(),
        policyNumber: policyLookup?.policy_number || "",
      });
      onUploaded(uploadRes.claim_id);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  const policyBanner = () => {
    if (!policyLookup) return null;

    if (policyLookup.loading) {
      return (
        <div className="flex items-center gap-2 text-xs text-blue-400 animate-pulse px-3 py-2 bg-blue-500/5 border border-blue-500/20 rounded-lg">
          <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          Verifying policy against records...
        </div>
      );
    }

    if (policyLookup.notFound) {
      return (
        <div className="flex items-start gap-2 px-3 py-2 bg-yellow-500/5 border border-yellow-500/20 rounded-lg text-xs text-yellow-400">
          <span className="mt-0.5">⚠</span>
          <span>
            No policy found for plate <strong>{policyLookup.plate}</strong>.
            You can still submit — a default policy will be used, or upload your policy document separately.
          </span>
        </div>
      );
    }

    const ok = policyLookup.match;
    return (
      <div className={`px-3 py-2.5 rounded-lg border text-xs ${
        ok
          ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-300"
          : "bg-red-500/5 border-red-500/20 text-red-400"
      }`}>
        <div className="flex items-center gap-2 mb-1">
          <span>{ok ? "✓" : "✕"}</span>
          <span className="font-semibold">{ok ? "Policy verified" : "Policy mismatch"}</span>
          <span className="ml-auto text-gray-500 font-mono">{policyLookup.policy_number}</span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-gray-400 mt-1">
          <span>Insured</span>
          <span className={policyLookup.name_match ? "text-emerald-300" : "text-red-400"}>
            {policyLookup.insured_name || "—"} {policyLookup.name_match ? "✓" : "✕"}
          </span>
          <span>Vehicle plate</span>
          <span className={policyLookup.plate_match ? "text-emerald-300" : "text-red-400"}>
            {policyLookup.vehicle_plate || "—"} {policyLookup.plate_match ? "✓" : "✕"}
          </span>
          {policyLookup.nric && (
            <>
              <span>NRIC on policy</span>
              <span className="font-mono text-gray-300">{policyLookup.nric}</span>
            </>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1.5">
          Extracted via SenseNova U1 · source: {policyLookup.source || "proxy"}
        </p>
      </div>
    );
  };

  if (publicShowcase) {
    return (
      <div>
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-1">Prepared Claims Review</h2>
          <p className="text-gray-400 text-sm">
            Explore three complete synthetic walkthroughs with staged signals and non-binding review receipts.
          </p>
        </div>

        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-5 text-sm text-amber-100">
          <p className="font-semibold uppercase tracking-widest text-xs text-amber-300">Synthetic and non-binding</p>
          <p className="mt-2 leading-relaxed">These examples do not request uploads, names, IDs, policy details, provider keys, or create a real claim. They never determine legal eligibility, coverage, liability, or a guaranteed payout.</p>
          <p className="mt-2 text-xs text-amber-200/80">The live operator workflow remains separately configured with its own server-side controls and is not available from this public showcase.</p>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {PREPARED_SCENARIOS.map((scenario) => (
            <article key={scenario.id} className="rounded-2xl border border-gray-800 bg-gray-900 p-5 flex flex-col">
              <p className="text-xs font-semibold uppercase tracking-widest text-blue-300">{scenario.path}</p>
              <h3 className="mt-2 text-lg font-bold text-white">{scenario.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-400 flex-1">{scenario.summary}</p>
              <p className="mt-4 text-xs leading-relaxed text-gray-500">Evidence: synthetic video, identity, policy, and audit signals.</p>
              <button
                type="button"
                onClick={() => onStartPreparedDemo(scenario)}
                className="mt-5 w-full rounded-xl bg-blue-600 py-3 font-bold text-white transition-all hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-300"
              >
                Explore {scenario.path.toLowerCase()} →
              </button>
            </article>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-1">File a New Claim</h2>
        <p className="text-gray-400 text-sm">
          Upload your dashcam footage and claimant details. Policy is verified automatically from your vehicle plate.
        </p>
        <p className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-200">
          Demonstration only. The public runner accepts only the published synthetic persona Jane Smith / SLD9775A / S9812381D. Footage is stored durably for the demo and processed by VideoDB; never submit personal data.
        </p>
        <button type="button" onClick={loadSampleFootage} disabled={loading} className="mt-3 rounded-lg border border-blue-500/40 bg-blue-500/10 px-4 py-2 text-xs font-semibold text-blue-200 hover:bg-blue-500/20">
          Load synthetic persona + sample footage
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Video upload zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
            dragging
              ? "border-blue-500 bg-blue-500/5"
              : file
              ? "border-green-500/50 bg-green-500/5"
              : "border-gray-700 hover:border-gray-600 bg-gray-900"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="video/*"
            className="hidden"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {file ? (
            <>
              <div className="text-3xl mb-2">🎬</div>
              <p className="text-green-400 font-semibold">{file.name}</p>
              <p className="text-gray-500 text-sm mt-1">
                {(file.size / (1024 * 1024)).toFixed(1)} MB — click to change
              </p>
            </>
          ) : (
            <>
              <div className="text-3xl mb-3 text-gray-600">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.361a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
                </svg>
              </div>
              <p className="text-gray-300 font-medium">Drop dashcam footage here</p>
              <p className="text-gray-500 text-sm mt-1">or click to browse — MP4, MOV, AVI</p>
            </>
          )}
        </div>

        {/* Claimant details */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-widest">Claimant Details</h3>

          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Full Name *</label>
            <input
              type="text"
              required
              value={form.claimantName}
              onChange={(e) => handleFieldChange("claimantName", e.target.value)}
              placeholder="Jane Smith"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">
                Vehicle Plate *
                <span className="ml-1 text-gray-600 font-normal normal-case tracking-normal">— used to locate your policy</span>
              </label>
              <input
                type="text"
                required
                value={form.vehiclePlate}
                onChange={(e) => handleFieldChange("vehiclePlate", e.target.value.toUpperCase())}
                placeholder="SLD9775A"
                maxLength={10}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors font-mono uppercase"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">National ID / License</label>
              <input
                type="text"
                value={form.claimantId}
                onChange={(e) => setForm({ ...form, claimantId: e.target.value })}
                placeholder="DL-123456"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1.5">
              NRIC / SingPass ID
              <span className="ml-2 text-gray-600 font-normal normal-case tracking-normal">
                — optional, triggers government identity verification
              </span>
            </label>
            <input
              type="text"
              value={form.nric}
              onChange={(e) => setForm({ ...form, nric: e.target.value.toUpperCase() })}
              placeholder="S9812381D"
              maxLength={9}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-600 focus:outline-none focus:border-purple-500 transition-colors font-mono"
            />
          </div>
        </div>

        {/* Policy verification banner — auto-populated from plate lookup */}
        {policyLookup !== null && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Policy Verification</span>
              <span className="text-xs text-gray-600">· SenseNova U1</span>
            </div>
            {policyBanner()}
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/40 disabled:cursor-not-allowed text-white font-bold py-3.5 rounded-xl transition-all"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Uploading...
            </span>
          ) : (
            "Run Synthetic Review →"
          )}
        </button>
      </form>

      <section className="mt-10 border-t border-gray-800 pt-8">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-gray-300">Or explore prepared reviews</h3>
        <p className="mt-2 text-xs text-gray-500">Instant, read-only examples remain available alongside the live synthetic workflow.</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {PREPARED_SCENARIOS.map((scenario) => (
            <button key={scenario.id} type="button" onClick={() => onStartPreparedDemo(scenario)} className="rounded-xl border border-gray-800 bg-gray-900 p-4 text-left hover:border-blue-500/50">
              <span className="text-xs font-semibold text-blue-300">{scenario.path}</span>
              <span className="mt-1 block text-sm font-bold text-white">{scenario.title}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Sponsor logos */}
      <div className="mt-8 pt-6 border-t border-gray-800">
        <p className="text-xs text-gray-600 text-center mb-3">Powered by</p>
        <div className="flex items-center justify-center gap-6 flex-wrap">
          {["VideoDB live video analysis", "OpenRouter live policy reasoning", "Azure PostgreSQL", "Vercel Blob", "Local policy engine"].map((s) => (
            <span key={s} className="text-xs text-gray-600 font-medium bg-gray-900 border border-gray-800 px-2.5 py-1 rounded">
              {s}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
