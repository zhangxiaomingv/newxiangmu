"use client";

import { useEffect, useState, use } from "react";
import { getAnalysis } from "@/lib/api";

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

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const result = await getAnalysis(id);
        if (cancelled) return;
        if (result.status === "completed") {
          setData(result);
          setLoading(false);
        } else if (result.status === "failed") {
          setError(result.progress || "Analysis failed");
          setLoading(false);
        } else {
          // Still running — poll again
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

  if (loading) return <LoadingSkeleton />;
  if (error) return <div className="flex flex-col items-center justify-center min-h-screen px-4 text-[#ff6040]">{error}</div>;
  if (!data) return <QuestionState />;

  const { score, score_breakdown, perception_profile, gap_map, suggestions, roadmap } = data;

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-10">
      {/* Header */}
      <div className="flex items-center justify-between animate-slide-up">
        <div>
          <a href="/" className="text-[#7c5cfc] text-sm hover:underline">&larr; New Analysis</a>
          <h1 className="text-2xl font-bold mt-2">{data.brand}</h1>
        </div>
      </div>

      {/* Module 1: AI Visibility Score */}
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
          </div>
        </div>
      </section>

      {/* Module 2: AI Perception Profile */}
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

      {/* Module 3: Gap Map */}
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

      {/* Module 4: Growth Suggestions */}
      <section className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 animate-slide-up" style={{ animationDelay: "0.4s" }}>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#7c5cfc]" />
          Recommended Actions
        </h2>
        <div className="space-y-3">
          {suggestions.map((s, i) => (
            <div key={i} className="p-4 bg-[#0a0a1a] rounded-xl border border-[#2a2a5a]/50">
              <div className="flex items-start justify-between gap-3 mb-1">
                <div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full mr-2 ${
                    s.priority === "immediate"
                      ? "bg-[#00e5a0]/10 text-[#00e5a0] border border-[#00e5a0]/30"
                      : "bg-[#7c5cfc]/10 text-[#b0a0ff] border border-[#7c5cfc]/30"
                  }`}>
                    {s.priority === "immediate" ? "⚡ 7 Days" : "📅 30 Days"}
                  </span>
                </div>
                <div className="flex gap-2 shrink-0">
                  <span className="text-xs text-[#666]">{effortBadge(s.effort)}</span>
                  <span className="text-xs text-[#666]">{impactBadge(s.impact)}</span>
                </div>
              </div>
              <p className="text-sm font-medium text-white mb-1">{s.title}</p>
              <p className="text-sm text-[#8888aa]">{s.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Module 5: AI Optimization Roadmap */}
      <section className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 animate-slide-up" style={{ animationDelay: "0.5s" }}>
        <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#00e5a0]" />
          Monitoring Timeline
        </h2>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[19px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-[#7c5cfc] via-[#00e5a0] to-[#7c5cfc]/30" />
          <div className="space-y-8">
            {roadmap.map((stage) => (
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
      </section>
    </div>
  );
}
