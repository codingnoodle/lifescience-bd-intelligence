export default function DiscoveryCard({ candidates, onRunDiligence }) {
  const statusStyle = {
    active: "bg-green-50 text-green-700",
    discontinued: "bg-red-50 text-red-600",
    partnered: "bg-blue-50 text-blue-700",
  };

  const statusLabel = {
    active: "Active",
    discontinued: "Discontinued",
    partnered: "Partnered",
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl mt-3 overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-center px-4 py-2.5 border-b border-gray-100">
        <span className="text-[11px] font-medium text-gray-400 tracking-wide">
          CANDIDATES · RANKED BY MATCH CONFIDENCE
        </span>
        <span className="text-[10px] text-gray-400">sorted by relevance</span>
      </div>

      {/* Candidate list */}
      {candidates.map((c, i) => (
        <div
          key={i}
          className="px-4 py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors"
        >
          {/* Title row */}
          <div className="flex justify-between items-start mb-1">
            <div>
              <span className="text-sm font-medium text-gray-900">{c.name}</span>
              {c.sponsor && (
                <span className="text-[11px] text-gray-400 ml-1.5">· {c.sponsor}</span>
              )}
            </div>
            {c.status && (
              <span
                className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ml-2 ${
                  statusStyle[c.status] || statusStyle.active
                }`}
              >
                {c.phase ? `${c.phase} ` : ""}
                {statusLabel[c.status] || c.status}
              </span>
            )}
          </div>

          {/* Details */}
          {c.details && (
            <div className="text-[11px] text-gray-500 leading-relaxed mb-2">{c.details}</div>
          )}

          {/* Meta chips */}
          {(c.target || c.trialId || c.sites || c.lastUpdate || c.historicalDeal) && (
            <div className="flex flex-wrap gap-3 text-[10px] text-gray-400 mb-2.5">
              {c.target && <span>Target: <strong className="text-gray-600">{c.target}</strong></span>}
              {c.trialId && <span>Trial ID: <strong className="text-gray-600">{c.trialId}</strong></span>}
              {c.sites && <span>Sites: <strong className="text-gray-600">{c.sites}</strong></span>}
              {c.lastUpdate && <span>Updated: <strong className="text-gray-600">{c.lastUpdate}</strong></span>}
              {c.historicalDeal && <span>Deal: <strong className="text-gray-600">{c.historicalDeal}</strong></span>}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex flex-wrap gap-1.5">
            {c.status !== "discontinued" && onRunDiligence && (
              <button
                onClick={() => onRunDiligence(c.name + (c.sponsor ? ` by ${c.sponsor}` : ""))}
                className="px-3 py-1 text-[11px] font-medium rounded-full bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 transition-colors"
              >
                Run full diligence →
              </button>
            )}
            {c.trialId && (
              <a
                href={`https://clinicaltrials.gov/study/${c.trialId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1 text-[11px] rounded-full border border-gray-200 text-gray-500 hover:bg-gray-100 transition-colors"
              >
                View trial details
              </a>
            )}
            {c.status === "discontinued" && onRunDiligence && (
              <button
                onClick={() => onRunDiligence(`benchmark ${c.name} as comp`)}
                className="px-3 py-1 text-[11px] rounded-full border border-gray-200 text-gray-500 hover:bg-gray-100 transition-colors"
              >
                See as comp benchmark
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
