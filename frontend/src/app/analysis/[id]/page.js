"use client";

import { useEffect, useState, use } from "react";
import { getAnalysis, reanalyze, getHistory } from "@/lib/api";

// ── Color helpers ───────────────────────────────────

function scoreColor(s) {
  if (s >= 70) return "text-[#00e5a0]";
  if (s >= 40) return "text-[#f0c040]";
  return "text-[#ff6040]";
}

function scoreBarColor(s) {
  if (s >= 70) return "bg-[#00e5a0]";
  if (s >= 40) return "bg-[#f0c040]";
  return "bg-[#ff6040]";
}

function severityColor(s) {
  if (s === "critical") return "bg-[#ff6040]/20 text-[#ff6040] border-[#ff6040]/30";
  if (s === "moderate") return "bg-[#f0c040]/20 text-[#f0c040] border-[#f0c040]/30";
  return "bg-[#00e5a0]/10 text-[#00e5a0] border-[#00e5a0]/20";
}

function effortBadge(e) {
  const m = { low: "🟢 Low", medium: "🟡 Medium", high: "🔴 High" };
  return m[e] || e;
}

function impactBadge(i) {
  const m = { low: "↓ Low", medium: "→ Medium", high: "↑ High" };
  return m[i] || i;
}

// ── SVG Sparkline (mini trend chart) ─────────────────

function ScoreSparkline({ history, currentScore }) {
  if (!history || history.length < 2) return null;
  const points = [...history].reverse(); // oldest → newest
  const scores = points.map(p => p.score);
  const min = Math.min(...scores, currentScore) - 10;
  const max = Math.max(...scores, currentScore) + 10;
  const range = max - min || 1;

  const W = 240, H = 40;
  const step = W / (points.length + 1);

  const line = points.map((p, i) => {
    const x = (i + 0.5) * step;
    const y = H - ((p.score - min) / range) * H;
    return `${i === 0 ? "M" : "L"}${x.toFixed(0)},${y.toFixed(0)}`;
  }).join(" ");

  // Current score dot
  const cx = (points.length + 0.5) * step;
  const cy = H - ((currentScore - min) / range) * H;

  return (
    <div className="flex items-center gap-4">
      <svg width={W} height={H} className="shrink-0">
        <path d={line} fill="none" stroke="#7c5cfc" strokeWidth="2" />
        <circle cx={cx} cy={cy} r="4" fill="#00e5a0" />
      </svg>
      <div className="text-xs text-[#8888aa]">
        <span className="text-white font-semibold">{points.length}</span> snapshots
        <br />
        <span className={scoreColor(currentScore)}>
          {currentScore >= (scores[scores.length - 1] || 0) ? "↑" : "↓"} trending
        </span>
      </div>
    </div>
  );
}

// ── Radial Gauge ────────────────────────────────────

function ScoreGauge({ score }) {
  const radius = 72;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (score / 100) * circ;

  return (
    <div className="flex flex-col items-center">
      <svg width="180" height="180" className="transform -rotate-90">
        <circle cx="90" cy="90" r={radius} fill="none" stroke="#2a2a5a" strokeWidth="10" />
        <circle
          cx="90" cy="90"
          r={radius}
          fill="none"
          stroke={score >= 70 ? "#00e5a0" : score >= 40 ? "#f0c040" : "#ff6040"}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className={`text-5xl font-bold ${scoreColor(score)}`}>{score}</span>
        <span className="text-xs text-[#8888aa] mt-1">out of 100</span>
      </div>
    </div>
  );
}

// ── Dimension Bar ───────────────────────────────────

function DimensionBar({ label, score, weight }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-24 text-sm text-[#8888aa] text-right shrink-0">{label}</div>
      <div className="flex-1 h-3 bg-[#1a1a3a] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${scoreBarColor(score)}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <div className={`text-sm font-mono w-10 text-right ${scoreColor(score)}`}>
        {score}
      </div>
      <div className="text-xs text-[#555] w-8">{Math.round(weight * 100)}%</div>
    </div>
  );
}

// ── Loading Skeleton ────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <span className="inline-block w-10 h-10 border-2 border-[#7c5cfc]/30 border-t-[#7c5cfc] rounded-full animate-spin mb-6" />
      <p className="text-[#8888aa] animate-pulse-glow">Analyzing AI perception...</p>
    </div>
  );
}

// ── Question Mark (waiting state) ───────────────────

function QuestionState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <span className="text-[#8888aa]">Analysis not found or still processing.</span>
    </div>
  );
}

// ── Main Page Component ──────────────────────────────

export default function AnalysisPage({ params }) {
  const { id } = use(params);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState(null);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [showActions, setShowActions] = useState("immediate");

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const result = await getAnalysis(id);
        if (cancelled) return;
        if (result.status === "completed") {
          setData(result);
          setLoading(false);
          // Load history in background
          getHistory(id).then(h => {
            if (!cancelled) setHistory(h);
          }).catch(() => {});
        } else if (result.status === "failed") {
          setError(result.progress || "Analysis failed");
          setLoading(false);
        } else {
          setTimeout(poll, 2000);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message);
          setLoading(false);
        }
      }
    }
    poll();
    return () => { cancelled = true; };
  }, [id]);

  async function handleReanalyze() {
    setReanalyzing(true);
    try {
      const result = await reanalyze(id);
      window.location.href = `/analysis/${result.id}`;
    } catch (e) {
      setError(e.message);
      setReanalyzing(false);
    }
  }

  if (loading) return <LoadingSkeleton />;
  if (error) return <div className="flex flex-col items-center justify-center min-h-screen px-4 text-[#ff6040]">{error}</div>;
  if (!data) return <QuestionState />;

  const { score, score_breakdown, perception_profile, gap_map, suggestions, roadmap } = data;

  // Latest roadmap items become our "Monitor timeline" stages
  const timelineStages = roadmap.length > 0 ? roadmap : [
    { stage: 1, title: "Foundation", description: "Basic AI recognition", actions: ["Add schema markup", "Optimize meta tags"] },
    { stage: 2, title: "Clarity", description: "Consistent AI understanding", actions: ["Clear value prop", "About page content"] },
    { stage: 3, title: "Authority", description: "AI trust signals", actions: ["Get press mentions", "Build backlinks"] },
    { stage: 4, title: "Rich Presence", description: "Multi-source consistency", actions: ["Knowledge graph", "Social proof"] },
    { stage: 5, title: "AI-native", description: "AI ecosystem optimized", actions: ["AI-friendly content", "API-first presence"] },
  ];

  const immediateActions = suggestions.filter(s => s.priority === "immediate");
  const mediumActions = suggestions.filter(s => s.priority === "medium_term");

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
      {/* ── Header ── */}
      <div className="flex items-center justify-between animate-slide-up">
        <div>
          <a href="/" className="text-[#7c5cfc] text-sm hover:underline">&larr; New Analysis</a>
          <h1 className="text-2xl font-bold mt-2 flex items-center gap-2">
            {data.brand}
            {history && history.length > 1 && (
              <span className="text-sm font-normal text-[#8888aa]">
                <span className={scoreColor(score)}>{score}</span>
                {" "}· <span className="text-[#555]">{history.length} scans</span>
              </span>
            )}
          </h1>
        </div>
        <button
          onClick={handleReanalyze}
          disabled={reanalyzing}
          className="px-4 py-2 bg-gradient-to-r from-[#7c5cfc] to-[#5a3fd4] text-white rounded-lg text-sm font-medium transition-all hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {reanalyzing ? (
            <>
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Scanning...
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10" />
                <polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
              Re-analyze
            </>
          )}
        </button>
      </div>

      {/* ── Module 1: AI Visibility Score ── */}
      <section className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 animate-slide-up" style={{ animationDelay: "0.1s" }}>
        <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#7c5cfc]" />
          AI Visibility
        </h2>
        <div className="flex flex-col md:flex-row items-center gap-10">
          <div className="relative flex items-center justify-center">
            <ScoreGauge score={score} />
          </div>
          <div className="flex-1 w-full space-y-3">
            {score_breakdown && Object.entries(score_breakdown).map(([key, val]) => {
              const weights = { mention: 0.2, consistency: 0.25, structure: 0.2, authority: 0.2, clarity: 0.15 };
              const labels = { mention: "Mention", consistency: "Consistency", structure: "Structure", authority: "Authority", clarity: "Clarity" };
              return (
                <DimensionBar key={key} label={labels[key] || key} score={val} weight={weights[key] || 0} />
              );
            })}
            {/* Sparkline if history available */}
            {history && history.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[#2a2a5a]">
                <ScoreSparkline history={history} currentScore={score} />
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── Module 2: AI Perception Profile ── */}
      <section className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 animate-slide-up" style={{ animationDelay: "0.2s" }}>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#00e5a0]" />
          AI Perception
        </h2>
        <p className="text-[#c0c0d0] leading-relaxed mb-6">{perception_profile.summary}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-medium text-[#8888aa] mb-2">Key Attributes</h3>
            <div className="flex flex-wrap gap-2">
              {perception_profile.key_attributes.map((a, i) => (
                <span key={i} className="px-3 py-1 text-sm bg-[#7c5cfc]/10 border border-[#7c5cfc]/30 rounded-full text-[#b0a0ff]">
                  {a}
                </span>
              ))}
            </div>
          </div>
          <div>
            <h3 className="text-sm font-medium text-[#8888aa] mb-2">Known For</h3>
            <ul className="space-y-1">
              {perception_profile.known_for.map((k, i) => (
                <li key={i} className="text-sm text-[#c0c0d0]">• {k}</li>
              ))}
            </ul>
          </div>
          {perception_profile.confusion_areas?.length > 0 && (
            <div className="md:col-span-2">
              <h3 className="text-sm font-medium text-[#ff6040] mb-2">Confusion Areas</h3>
              <ul className="space-y-1">
                {perception_profile.confusion_areas.map((c, i) => (
                  <li key={i} className="text-sm text-[#c0c0d0]">⚠ {c}</li>
                ))}
              </ul>
            </div>
          )}
          {perception_profile.competitor_context && (
            <div className="md:col-span-2">
              <h3 className="text-sm font-medium text-[#8888aa] mb-1">Competitive Context</h3>
              <p className="text-sm text-[#c0c0d0]">{perception_profile.competitor_context}</p>
            </div>
          )}
        </div>
      </section>

      {/* ── Module 3: Gap Map ── */}
      <section className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 animate-slide-up" style={{ animationDelay: "0.3s" }}>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#f0c040]" />
          Missing Signals
        </h2>
        <div className="space-y-3">
          {gap_map.map((gap, i) => (
            <div key={i} className="flex items-start gap-4 p-4 bg-[#0a0a1a] rounded-xl border border-[#2a2a5a]/50">
              <div className="w-2 h-2 rounded-full mt-1.5 shrink-0 bg-current"
                style={{ color: gap.severity === "critical" ? "#ff6040" : gap.severity === "moderate" ? "#f0c040" : "#00e5a0" }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${severityColor(gap.severity)}`}>
                    {gap.severity}
                  </span>
                  <span className="text-xs text-[#555] uppercase">{gap.category}</span>
                </div>
                <p className="text-sm text-[#c0c0d0]">{gap.description}</p>
                {gap.evidence && (
                  <p className="text-xs text-[#666688] mt-1 italic">{gap.evidence}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Module 4: Recommended Actions ── */}
      <section className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 animate-slide-up" style={{ animationDelay: "0.4s" }}>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#7c5cfc]" />
          Recommended Actions
        </h2>

        {/* Tabs: Immediate / Medium Term */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setShowActions("immediate")}
            className={`px-4 py-1.5 text-sm rounded-lg transition-all ${
              showActions === "immediate"
                ? "bg-[#00e5a0]/15 text-[#00e5a0] border border-[#00e5a0]/30"
                : "bg-[#0a0a1a] text-[#8888aa] border border-[#2a2a5a] hover:border-[#555]"
            }`}
          >
            ⚡ Immediate (7 days)
            {immediateActions.length > 0 && (
              <span className="ml-1.5 text-xs opacity-60">({immediateActions.length})</span>
            )}
          </button>
          <button
            onClick={() => setShowActions("medium")}
            className={`px-4 py-1.5 text-sm rounded-lg transition-all ${
              showActions === "medium"
                ? "bg-[#7c5cfc]/15 text-[#b0a0ff] border border-[#7c5cfc]/30"
                : "bg-[#0a0a1a] text-[#8888aa] border border-[#2a2a5a] hover:border-[#555]"
            }`}
          >
            📅 Medium Term (30 days)
            {mediumActions.length > 0 && (
              <span className="ml-1.5 text-xs opacity-60">({mediumActions.length})</span>
            )}
          </button>
        </div>

        <div className="space-y-3">
          {(showActions === "immediate" ? immediateActions : mediumActions).map((s, i) => (
            <div key={i} className="p-4 bg-[#0a0a1a] rounded-xl border border-[#2a2a5a]/50">
              <div className="flex items-start justify-between gap-3 mb-1">
                <p className="text-sm font-medium text-white">{s.title}</p>
                <div className="flex gap-2 shrink-0">
                  <span className="text-xs text-[#666]">{effortBadge(s.effort)}</span>
                  <span className="text-xs text-[#666]">{impactBadge(s.impact)}</span>
                </div>
              </div>
              <p className="text-sm text-[#8888aa]">{s.description}</p>
            </div>
          ))}
          {(showActions === "immediate" ? immediateActions : mediumActions).length === 0 && (
            <p className="text-sm text-[#555] text-center py-4">No suggestions in this category.</p>
          )}
        </div>
      </section>

      {/* ── Module 5: Monitoring Timeline ── */}
      <section className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 animate-slide-up" style={{ animationDelay: "0.5s" }}>
        <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#00e5a0]" />
          {history && history.length > 1 ? "Monitoring Timeline" : "AI Optimization Roadmap"}
          {history && history.length > 1 && (
            <span className="text-xs font-normal text-[#8888aa] ml-auto">
              Last scan: {new Date(history[0].created_at).toLocaleDateString()}
            </span>
          )}
        </h2>

        {history && history.length > 1 ? (
          /* ── Score History Timeline ── */
          <div className="relative">
            <div className="absolute left-[19px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-[#7c5cfc] via-[#00e5a0] to-[#7c5cfc]/30" />
            <div className="space-y-6">
              {history.map((snap, i) => {
                const date = new Date(snap.created_at);
                const localDate = date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
                const localTime = date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
                const prevScore = i < history.length - 1 ? history[i + 1].score : score;
                const delta = snap.score - prevScore;
                return (
                  <div key={i} className="relative pl-12">
                    <div className={`absolute left-2.5 top-1 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2
                      ${snap.score >= 70 ? "bg-[#00e5a0]/20 border-[#00e5a0] text-[#00e5a0]"
                        : snap.score >= 40 ? "bg-[#f0c040]/20 border-[#f0c040] text-[#f0c040]"
                        : "bg-[#ff6040]/20 border-[#ff6040] text-[#ff6040]"
                      }`}
                    >
                      {snap.score}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-[#8888aa]">{localDate}</span>
                        <span className="text-xs text-[#555]">{localTime}</span>
                        {i === 0 && (
                          <span className="text-xs text-[#00e5a0] bg-[#00e5a0]/10 px-2 py-0.5 rounded-full">latest</span>
                        )}
                        {delta !== 0 && i > 0 && (
                          <span className={`text-xs ${delta > 0 ? "text-[#00e5a0]" : "text-[#ff6040]"}`}>
                            {delta > 0 ? "↑" : "↓"} {Math.abs(delta).toFixed(1)}
                          </span>
                        )}
                      </div>
                      {/* Mini dimension bars */}
                      <div className="mt-2 flex gap-3 flex-wrap">
                        {Object.entries(snap.score_breakdown).map(([k, v]) => (
                          <span key={k} className="text-xs text-[#666688]">
                            {k}: <span className={scoreColor(v)}>{v}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          /* ── Fallback: Static Roadmap ── */
          <div className="relative">
            <div className="absolute left-[19px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-[#7c5cfc] via-[#00e5a0] to-[#7c5cfc]/30" />
            <div className="space-y-8">
              {timelineStages.map((stage) => (
                <div key={stage.stage} className="relative pl-12">
                  <div className={`absolute left-2.5 top-1 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2
                    ${stage.stage <= 2 ? "bg-[#7c5cfc]/20 border-[#7c5cfc] text-[#7c5cfc]"
                      : stage.stage <= 4 ? "bg-[#00e5a0]/20 border-[#00e5a0] text-[#00e5a0]"
                      : "bg-[#7c5cfc]/10 border-[#8888aa] text-[#8888aa]"
                    }`}
                  >
                    {stage.stage}
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">{stage.title}</h3>
                    <p className="text-sm text-[#8888aa] mb-2">{stage.description}</p>
                    <ul className="space-y-1">
                      {stage.actions.map((a, i) => (
                        <li key={i} className="text-sm text-[#c0c0d0] flex items-start gap-2">
                          <span className="text-[#555] mt-0.5">→</span>
                          {a}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
