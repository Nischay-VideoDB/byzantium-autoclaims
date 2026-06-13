export default function Header() {
  return (
    <header className="border-b border-gray-800 mb-8">
      <div className="max-w-3xl mx-auto px-4 py-5 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white text-lg select-none">
          BY
        </div>
        <div>
          <h1 className="text-lg font-bold text-white leading-none">Byzantium AutoClaims</h1>
          <p className="text-xs text-gray-400 mt-0.5">Autonomous Insurance Claims Approval with Trust Validation</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          <span className="text-xs text-gray-400">Live</span>
        </div>
      </div>
    </header>
  );
}
