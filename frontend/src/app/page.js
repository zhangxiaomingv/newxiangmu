"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { startAnalysis } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [brand, setBrand] = useState("");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!brand.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await startAnalysis(brand.trim(), url.trim() || null);
      router.push(`/analysis/${result.id}`);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-20">
      {/* Header */}
      <div className="text-center mb-12 animate-slide-up max-w-2xl">
        <h1 className="text-5xl font-bold mb-4 tracking-tight leading-tight">
          <span className="bg-gradient-to-r from-[#7c5cfc] to-[#00e5a0] bg-clip-text text-transparent">
            See Your Brand Through AI
          </span>
        </h1>
        <p className="text-base text-[#8888aa] leading-relaxed max-w-lg mx-auto">
          Understand how AI models perceive your brand, identify what is missing,
          and continuously improve your AI visibility.
        </p>
        <p className="text-sm text-[#8888aa]/60 mt-4 italic">
          ZKoner 帮助品牌理解 AI 如何认识自己，并持续优化这种认知
        </p>
        <p className="text-xs text-[#555]/60 mt-1">
          使命：让每一个品牌都能建立、监测和优化自己在 AI 世界中的认知
        </p>
      </div>

      {/* Input Form */}
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-xl space-y-4 animate-slide-up"
        style={{ animationDelay: "0.1s" }}
      >
        <div className="relative">
          <input
            type="text"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder="Brand name or URL (e.g., Anthropic, tesla.com)"
            className="w-full px-5 py-4 bg-[#12122a] border border-[#2a2a5a] rounded-xl text-white placeholder-[#666688] outline-none focus:border-[#7c5cfc] focus:ring-1 focus:ring-[#7c5cfc] transition-all text-lg"
            disabled={loading}
            autoFocus
          />
        </div>

        <div className="relative">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://yourbrand.com"
            className="w-full px-5 py-3 bg-[#12122a] border border-[#2a2a5a] rounded-xl text-white placeholder-[#666688] outline-none focus:border-[#7c5cfc] focus:ring-1 focus:ring-[#7c5cfc] transition-all"
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !brand.trim()}
          className="w-full py-4 bg-gradient-to-r from-[#7c5cfc] to-[#5a3fd4] text-white rounded-xl font-semibold text-lg transition-all hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <span className="inline-block w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Analyzing...
            </>
          ) : (
            "Analyze Your Brand"
          )}
        </button>

        {error && (
          <div className="text-[#ff6040] text-sm text-center bg-[#ff6040]/10 rounded-lg px-4 py-3">
            {error}
          </div>
        )}
      </form>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 w-full max-w-3xl animate-slide-up" style={{ animationDelay: "0.3s" }}>
        {[
          { label: "ZKoner Scan", desc: "AI detection & visibility analysis" },
          { label: "ZKoner Insight", desc: "AI cognition & entity analysis" },
          { label: "ZKoner Action", desc: "Improvement & content suggestions" },
        ].map((f) => (
          <div
            key={f.label}
            className="bg-[#12122a] border border-[#2a2a5a] rounded-xl p-5 text-center hover:border-[#7c5cfc]/40 transition-all"
          >
            <div className="text-[#7c5cfc] text-lg font-semibold mb-1">{f.label}</div>
            <div className="text-[#8888aa] text-sm">{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
