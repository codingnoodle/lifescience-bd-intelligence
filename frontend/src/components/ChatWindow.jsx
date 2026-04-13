import { useState, useRef, useEffect, useCallback } from "react";
import { Search, FlaskConical, Activity, TrendingUp, House, Info, X, Zap, Shield, BarChart3 } from "lucide-react";
import ResultCard from "./ResultCard";
import DiscoveryCard from "./DiscoveryCard";
import GuidedEntryForm from "./GuidedEntryForm";

// ── Card definitions ────────────────────────────────────────────────────────
const USE_CASE_CARDS = [
  {
    id: "deep-dive",
    icon: Search,
    iconBg: "#E6F1FB",
    iconColor: "#185FA5",
    title: "Deep-dive a known asset",
    desc: "Full diligence on a specific drug — science profile, comparator analysis, three-scenario valuation, and likely buyers.",
    example: "e.g. tovorafenib Day One BRAF glioma Phase 3",
    action: "prefill",
    prefill: "tovorafenib Day One BRAF glioma Phase 3",
  },
  {
    id: "preclinical",
    icon: FlaskConical,
    iconBg: "#FAEEDA",
    iconColor: "#854F0B",
    title: "Explore a preclinical asset",
    desc: "Limited public data? The system benchmarks against similar MOAs, phases, and recent deal archetypes.",
    example: "e.g. ROR1 ADC, preclinical",
    action: "guided",
  },
  {
    id: "scan-ta",
    icon: Activity,
    iconBg: "#E1F5EE",
    iconColor: "#0F6E56",
    title: "Scan a therapeutic area",
    desc: "Surface the top pipeline candidates in any TA and phase, ranked by commercial potential.",
    example: "e.g. top Ph2 oncology assets, 2028 launch",
    action: "prefill",
    prefill: "top Phase 2 oncology assets launching 2028",
  },
  {
    id: "benchmark",
    icon: TrendingUp,
    iconBg: "#EEEDFE",
    iconColor: "#3C3489",
    title: "Benchmark vs recent deals",
    desc: "Compare any asset to 2025-2026 M&A comps — see where it lands on the deal multiple spectrum.",
    example: "e.g. benchmark ARV-471 vs recent PROTAC deals",
    action: "prefill",
    prefill: "benchmark ARV-471 vs recent PROTAC deals in oncology",
  },
];

const QUICK_STARTS = [
  { label: "TERN-701 (CML, Ph1/2)", query: "TERN-701 allosteric BCR::ABL1 TKI CML Phase 1/2" },
  { label: "Centessa ORX750 (narcolepsy)", query: "Centessa Pharmaceuticals cleminorexton ORX750 Phase 2a NT1 NT2 IH breakthrough designation" },
  { label: "Metsera GLP-1 (obesity)", query: "Metsera ultra-long-acting GLP-1 obesity Phase 2b" },
];

// ── Sub-components ───────────────────────────────────────────────────────────
function UserBubble({ text }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-xs lg:max-w-md bg-blue-50 text-blue-800 text-sm px-4 py-2 rounded-2xl rounded-tr-sm leading-relaxed">
        {text}
      </div>
    </div>
  );
}

function BotBubble({ text, result, onAction, onRecalculate }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-full lg:max-w-3xl bg-gray-50 border border-gray-200 text-gray-800 text-sm px-4 py-3 rounded-2xl rounded-tl-sm leading-relaxed">
        <p>{text}</p>
        {result?.discoveryMode && result.candidates ? (
          <DiscoveryCard candidates={result.candidates} onRunDiligence={onAction} />
        ) : result ? (
          <ResultCard result={result} onRecalculate={onRecalculate} />
        ) : null}
      </div>
    </div>
  );
}

function StatusIndicator({ status }) {
  return (
    <div className="flex justify-start">
      <div className="bg-gray-50 border border-gray-200 px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-2">
        <div className="flex gap-1 items-center">
          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
        <span className="text-xs text-gray-400">{status}</span>
      </div>
    </div>
  );
}

function WelcomeScreen({ onCardClick, onQuickStart }) {
  return (
    <div className="flex-1 overflow-y-auto flex flex-col items-center justify-start px-5 py-6 gap-6">
      {/* Hero */}
      <div className="max-w-lg text-center mt-4">
        <div className="text-xl font-semibold text-gray-900 mb-2 leading-tight">
          Pharma BD Decision Intelligence
        </div>
        <div className="text-sm text-gray-500 leading-relaxed max-w-md mx-auto">
          Evaluate any drug asset in minutes. Get science scores, comparator analysis,
          three-scenario deal pricing, and likely buyer mapping — all grounded in
          2025-2026 M&A benchmarks.
        </div>
      </div>

      {/* Value props */}
      <div className="flex gap-6 max-w-lg">
        <div className="flex items-start gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center shrink-0 mt-0.5">
            <Zap size={13} className="text-blue-600" />
          </div>
          <div>
            <div className="text-[12px] font-medium text-gray-800">Dual-view valuation</div>
            <div className="text-[11px] text-gray-400 leading-relaxed">Risk-adjusted NPV and if-succeed scenarios side by side</div>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <div className="w-7 h-7 rounded-lg bg-green-50 flex items-center justify-center shrink-0 mt-0.5">
            <Shield size={13} className="text-green-600" />
          </div>
          <div>
            <div className="text-[12px] font-medium text-gray-800">Every assumption editable</div>
            <div className="text-[11px] text-gray-400 leading-relaxed">Override PTRS, comparators, or buyers and recalculate instantly</div>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <div className="w-7 h-7 rounded-lg bg-purple-50 flex items-center justify-center shrink-0 mt-0.5">
            <BarChart3 size={13} className="text-purple-600" />
          </div>
          <div>
            <div className="text-[12px] font-medium text-gray-800">Buyer urgency mapping</div>
            <div className="text-[11px] text-gray-400 leading-relaxed">Patent cliffs, deal velocity, and bidding tension scored</div>
          </div>
        </div>
      </div>

      {/* Divider with label */}
      <div className="flex items-center gap-3 w-full max-w-[580px]">
        <div className="flex-1 border-t border-gray-200" />
        <span className="text-[10px] text-gray-400 tracking-widest font-medium">CHOOSE A WORKFLOW</span>
        <div className="flex-1 border-t border-gray-200" />
      </div>

      {/* Use case cards */}
      <div className="grid grid-cols-2 gap-2.5 max-w-[580px] w-full">
        {USE_CASE_CARDS.map((card) => {
          const Icon = card.icon;
          return (
            <button
              key={card.id}
              onClick={() => onCardClick(card)}
              className="text-left bg-white border border-gray-200 rounded-xl p-3.5 cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all flex flex-col gap-1 group"
            >
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center mb-0.5"
                style={{ background: card.iconBg, color: card.iconColor }}
              >
                <Icon size={14} />
              </div>
              <div className="text-[13px] font-medium text-gray-900">{card.title}</div>
              <div className="text-[11px] text-gray-500 leading-[1.5]">{card.desc}</div>
              <div className="text-[10px] text-gray-400 mt-1 font-mono group-hover:text-blue-400 transition-colors">{card.example}</div>
            </button>
          );
        })}
      </div>

      {/* Quick starts */}
      <div className="max-w-[580px] w-full">
        <div className="text-[10px] text-gray-400 tracking-widest font-medium mb-2">TRY AN EXAMPLE</div>
        <div className="flex flex-wrap gap-1.5">
          {QUICK_STARTS.map((qs) => (
            <button
              key={qs.label}
              onClick={() => onQuickStart(qs.query)}
              className="text-[11px] px-3 py-1.5 rounded-full border border-gray-200 text-gray-500 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-all cursor-pointer"
            >
              {qs.label}
            </button>
          ))}
        </div>
      </div>

      {/* Footer note */}
      <div className="text-[10px] text-gray-300 max-w-md text-center leading-relaxed mt-2">
        Powered by multi-agent analysis (science, market, synthesis). Valuations are estimates for
        diligence purposes — not investment advice. All assumptions are transparent and editable.
      </div>
    </div>
  );
}

// ── Scoring Rubric panel ─────────────────────────────────────────────────────
function ScoringRubric({ onClose }) {
  return (
    <div className="absolute inset-y-0 right-0 w-80 bg-white border-l border-gray-200 shadow-lg z-20 flex flex-col overflow-hidden">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <span className="text-sm font-medium text-gray-900">Scoring Rubric</span>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-700 transition-colors">
          <X size={15} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-5 text-xs text-gray-600">

        {/* Composite score */}
        <div>
          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-2">COMPOSITE SCORE</div>
          <div className="bg-gray-50 rounded-lg px-3 py-3 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Science quality</span>
              <span className="font-semibold text-blue-700">60%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Market attractiveness</span>
              <span className="font-semibold text-purple-700">40%</span>
            </div>
            <div className="border-t border-gray-200 pt-2 flex items-center justify-between font-medium text-gray-800">
              <span>Composite (0 – 10)</span>
              <span className="font-mono text-xs bg-gray-200 px-2 py-0.5 rounded">0.6 × sci + 0.4 × mkt</span>
            </div>
          </div>
        </div>

        {/* GO / WATCH / NO-GO */}
        <div>
          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-2">RECOMMENDATION THRESHOLDS</div>
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              <span className="font-semibold text-green-700 text-sm">GO</span>
              <span className="text-green-700">Score ≥ 6.5</span>
            </div>
            <div className="flex items-center justify-between bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              <span className="font-semibold text-amber-700 text-sm">WATCH</span>
              <span className="text-amber-700">4.5 – 6.4</span>
            </div>
            <div className="flex items-center justify-between bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <span className="font-semibold text-red-700 text-sm">NO-GO</span>
              <span className="text-red-700">Score &lt; 4.5</span>
            </div>
          </div>
        </div>

        {/* Science agent */}
        <div>
          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-2">SCIENCE AGENT (0 – 10)</div>
          <div className="bg-gray-50 rounded-lg px-3 py-3 leading-relaxed text-gray-600">
            Searches PubMed, FDA, NEJM, ClinicalTrials.gov for clinical evidence. Scores on:
            <ul className="mt-1.5 ml-3 list-disc flex flex-col gap-1">
              <li>Clinical trial design & endpoints</li>
              <li>Efficacy data (ORR, PFS, OS)</li>
              <li>Mechanism differentiation vs. SOC</li>
              <li>Safety / tolerability profile</li>
              <li>Regulatory pathway clarity</li>
            </ul>
          </div>
        </div>

        {/* Market agent */}
        <div>
          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-2">MARKET AGENT (0 – 10)</div>
          <div className="bg-gray-50 rounded-lg px-3 py-3 leading-relaxed text-gray-600">
            Searches EvaluatePharma, BioPharma Dive, SEC filings. Scores on:
            <ul className="mt-1.5 ml-3 list-disc flex flex-col gap-1">
              <li>Addressable patient population</li>
              <li>Competitive landscape & white space</li>
              <li>Pricing / reimbursement precedents</li>
              <li>Comparable deal benchmarks</li>
            </ul>
          </div>
        </div>

        {/* Three-scenario valuation */}
        <div>
          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-2">THREE-SCENARIO VALUATION</div>
          <div className="bg-gray-50 rounded-lg px-3 py-3 flex flex-col gap-2.5 leading-relaxed">
            <div>
              <span className="font-medium text-gray-600">1. Standalone NPV</span>
              <div className="font-mono text-[11px] bg-white border border-gray-200 rounded px-2 py-1 mt-1">
                Σ(peak_standalone × PTRS_adj × NPV_discount)
              </div>
            </div>
            <div>
              <span className="font-medium text-blue-600">2. Platform + displacement</span>
              <div className="font-mono text-[11px] bg-white border border-gray-200 rounded px-2 py-1 mt-1">
                Σ(peak_displacement × PTRS_adj × NPV_discount)
              </div>
              <div className="text-[10px] text-gray-400 mt-0.5">
                Includes SOC capture if best/better-in-class, or category expansion if new_class_creation.
              </div>
            </div>
            <div>
              <span className="font-medium text-green-600">3. Strategic buyer premium</span>
              <div className="font-mono text-[11px] bg-white border border-gray-200 rounded px-2 py-1 mt-1">
                platform × buyer_urgency × (1 + bidding_premium)
              </div>
              <div className="text-[10px] text-gray-400 mt-0.5">
                Buyer urgency from patent cliff + flush capital. Bidding premium from analyst coverage, capable buyer count, TA deal velocity.
              </div>
            </div>
          </div>
        </div>

        {/* PTRS table */}
        <div>
          <div className="text-[11px] font-medium text-gray-400 tracking-wide mb-2">PTRS BY PHASE (ONCOLOGY)</div>
          <table className="w-full text-[11px]">
            <thead>
              <tr className="text-gray-400 border-b border-gray-100">
                <th className="text-left pb-1 font-medium">Phase</th>
                <th className="text-right pb-1 font-medium">Oncology</th>
                <th className="text-right pb-1 font-medium">Other TA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[
                ["Preclinical", "5%", "8%"],
                ["Phase 1", "10%", "13%"],
                ["Phase 2", "25%", "28%"],
                ["Phase 3", "55%", "60%"],
                ["NDA / BLA", "85%", "88%"],
              ].map(([phase, onc, other]) => (
                <tr key={phase} className="text-gray-600">
                  <td className="py-1">{phase}</td>
                  <td className="text-right py-1 font-mono">{onc}</td>
                  <td className="text-right py-1 font-mono">{other}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export default function ChatWindow({ filters, input, onInputChange }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [mode, setMode] = useState("chat"); // "chat" | "guided"
  const [showRubric, setShowRubric] = useState(false);
  const bottomRef = useRef(null);

  const isWelcome = messages.length === 0 && !loading;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, status]);

  // Core send logic — accepts text directly
  const sendMessageWithText = async (text) => {
    if (!text.trim() || loading) return;
    setMode("chat");

    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);
    setStatus("Connecting to analysis engine...");

    try {
      const res = await fetch("http://localhost:8000/analyze/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, filters }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          let event;
          try { event = JSON.parse(raw); } catch { continue; }

          if (event.type === "progress") {
            setStatus(event.message);
          } else if (event.type === "done") {
            setMessages((prev) => [
              ...prev,
              { role: "bot", text: event.message, result: event.result || null },
            ]);
            setLoading(false);
            setStatus("");
          } else if (event.type === "error") {
            setMessages((prev) => [
              ...prev,
              { role: "bot", text: `Error: ${event.message}`, result: null },
            ]);
            setLoading(false);
            setStatus("");
          }
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: "Something went wrong connecting to the analysis engine. Please try again.",
          result: null,
        },
      ]);
      setLoading(false);
      setStatus("");
    }
  };

  const sendMessage = () => {
    const text = (input || "").trim();
    onInputChange("");
    sendMessageWithText(text);
  };

  // Recalculate handler — re-runs from market agent onward with user override
  const handleRecalculate = useCallback(async (override, msgIndex) => {
    const msg = messages[msgIndex];
    if (!msg?.result?.assetName) return;

    setLoading(true);
    setStatus("Recalculating with your override...");
    try {
      const res = await fetch("http://localhost:8000/recalculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_name: msg.result.assetName,
          indications: msg.result.indications,
          overrides: override,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessages((prev) => {
        const updated = [...prev];
        updated[msgIndex] = { ...updated[msgIndex], text: data.message, result: data.result };
        return updated;
      });
    } catch (err) {
      console.error("Recalculate failed:", err);
    } finally {
      setLoading(false);
      setStatus("");
    }
  }, [messages]);

  const resetToWelcome = () => {
    setMessages([]);
    setMode("chat");
    onInputChange("");
  };

  const handleCardClick = (card) => {
    if (card.action === "guided") {
      setMode("guided");
    } else if (card.action === "prefill") {
      onInputChange(card.prefill);
    }
  };

  const handleGuidedSubmit = (query) => {
    onInputChange("");
    sendMessageWithText(query);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col flex-1 overflow-hidden relative">
      {/* Scoring rubric panel */}
      {showRubric && <ScoringRubric onClose={() => setShowRubric(false)} />}

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-green-400 ring-2 ring-green-100" />
          <div>
            <div className="text-sm font-medium text-gray-900">BD Decision Intelligence</div>
            <div className="text-[11px] text-gray-400">
              {mode === "guided"
                ? "Guided entry · preclinical asset"
                : isWelcome
                ? "Multi-agent pharma asset valuation"
                : "Analysis in progress"}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!isWelcome && (
            <button
              onClick={() => setShowRubric((v) => !v)}
              title="Scoring rubric"
              className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg transition-colors cursor-pointer ${
                showRubric
                  ? "bg-blue-50 text-blue-600"
                  : "text-gray-400 hover:text-gray-700 hover:bg-gray-100"
              }`}
            >
              <Info size={13} />
              <span>Methodology</span>
            </button>
          )}
          {!isWelcome && (
            <button
              onClick={resetToWelcome}
              title="Back to home"
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-700 px-2.5 py-1.5 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
            >
              <House size={13} />
              <span>Home</span>
            </button>
          )}
        </div>
      </div>

      {/* Body: welcome / guided form / chat */}
      {mode === "guided" && isWelcome ? (
        <GuidedEntryForm
          onSubmit={handleGuidedSubmit}
          onBack={() => setMode("chat")}
        />
      ) : isWelcome ? (
        <WelcomeScreen onCardClick={handleCardClick} onQuickStart={(q) => sendMessageWithText(q)} />
      ) : (
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {messages.map((msg, i) =>
            msg.role === "user" ? (
              <UserBubble key={i} text={msg.text} />
            ) : (
              <BotBubble
                key={i}
                text={msg.text}
                result={msg.result}
                onAction={(query) => sendMessageWithText(query)}
                onRecalculate={(override) => handleRecalculate(override, i)}
              />
            )
          )}
          {loading && <StatusIndicator status={status} />}
          <div ref={bottomRef} />
        </div>
      )}

      {/* Input row — shown in all modes except guided welcome */}
      {!(mode === "guided" && isWelcome) && (
        <div className="flex gap-2 px-3 py-3 border-t border-gray-200">
          {/* Mode toggle */}
          {isWelcome && (
            <div className="flex bg-gray-100 rounded-full p-0.5 text-[11px] shrink-0">
              <button
                onClick={() => setMode("chat")}
                className={`px-3 py-1 rounded-full transition-colors ${
                  mode === "chat"
                    ? "bg-white text-gray-800 font-medium shadow-sm"
                    : "text-gray-500"
                }`}
              >
                Quick chat
              </button>
              <button
                onClick={() => setMode("guided")}
                className={`px-3 py-1 rounded-full transition-colors ${
                  mode === "guided"
                    ? "bg-white text-gray-800 font-medium shadow-sm"
                    : "text-gray-500"
                }`}
              >
                Guided
              </button>
            </div>
          )}

          <input
            className="flex-1 text-sm px-4 py-2 rounded-full border border-gray-200 bg-gray-50 outline-none focus:border-blue-300 focus:bg-white transition-colors"
            placeholder={
              isWelcome
                ? "Type any drug asset + indication, e.g. tovorafenib BRAF glioma Phase 3"
                : "Ask a follow-up or enter another asset..."
            }
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !(input || "").trim()}
            className="px-4 py-2 rounded-full border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Send ↗
          </button>
        </div>
      )}
    </div>
  );
}
