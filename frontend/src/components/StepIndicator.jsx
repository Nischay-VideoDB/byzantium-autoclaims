export default function StepIndicator({ steps, current }) {
  return (
    <div className="flex items-center mb-10 px-1">
      {steps.map((label, i) => (
        <div key={i} className="flex items-center flex-1 last:flex-none">
          <div className="flex flex-col items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                i < current
                  ? "bg-blue-600 text-white"
                  : i === current
                  ? "bg-blue-500 text-white ring-2 ring-blue-400 ring-offset-2 ring-offset-gray-950"
                  : "bg-gray-800 text-gray-500"
              }`}
            >
              {i < current ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                i + 1
              )}
            </div>
            <span
              className={`mt-1.5 text-xs font-medium ${
                i <= current ? "text-gray-200" : "text-gray-600"
              }`}
            >
              {label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div
              className={`flex-1 h-px mx-2 mb-4 transition-all ${
                i < current ? "bg-blue-600" : "bg-gray-800"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}
