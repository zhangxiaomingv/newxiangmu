"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslations, useLocale } from "next-intl";
import { startAnalysis, getRecent } from "@/lib/api";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function Home() {
  const router = useRouter();
  const t = useTranslations();
  const locale = useLocale();
  const [brand, setBrand] = useState("");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    getRecent().then(setRecent).catch(() => {});
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!brand.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await startAnalysis(brand.trim(), url.trim() || null, locale);
      const prefix = locale === "en" ? "" : `/${locale}`;
      router.push(`${prefix}/analysis/${result.id}`);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-20">
      {/* Language Switcher */}
      <div className="fixed top-4 right-4 z-50">
        <LanguageSwitcher />
      </div>

      {/* Header */}
      <div className="text-center mb-12 animate-slide-up max-w-2xl">
        <h1 className="text-5xl font-bold mb-4 tracking-tight leading-tight">
          <span className="bg-gradient-to-r from-[#7c5cfc] to-[#00e5a0] bg-clip-text text-transparent">
            {t("hero.title")}
          </span>
        </h1>
        <p className="text-base text-[#8888aa] leading-relaxed max-w-lg mx-auto">
          {t("hero.subtitle")}
        </p>
        <p className="text-sm text-[#8888aa]/60 mt-4 italic">
          {t("hero.chineseTagline")}
        </p>
        <p className="text-xs text-[#555]/60 mt-1">
          {t("hero.mission")}
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
            placeholder={t("form.brandPlaceholder")}
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
            placeholder={t("form.urlPlaceholder")}
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
              {t("form.analyzing")}
            </>
          ) : (
            t("form.analyzeButton")
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
          { key: "scan" },
          { key: "insight" },
          { key: "action" },
        ].map((f) => (
          <div
            key={f.key}
            className="bg-[#12122a] border border-[#2a2a5a] rounded-xl p-5 text-center hover:border-[#7c5cfc]/40 transition-all"
          >
            <div className="text-[#7c5cfc] text-lg font-semibold mb-1">
              ZKoner {t(`features.${f.key}.title`)}
            </div>
            <div className="text-[#8888aa] text-sm">
              {t(`features.${f.key}.desc`)}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Analyses */}
      {recent.length > 0 && (
        <div className="w-full max-w-3xl mt-8 animate-slide-up" style={{ animationDelay: "0.5s" }}>
          <h3 className="text-sm font-medium text-[#8888aa] mb-3">{t("recent.title")}</h3>
          <div className="space-y-2">
            {recent.slice(0, 5).map((r) => (
              <a
                key={r.id}
                href={`/analysis/${r.id}`}
                className="flex items-center justify-between p-3 bg-[#12122a] border border-[#2a2a5a] rounded-lg hover:border-[#7c5cfc]/40 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${
                    r.status === "completed" ? "bg-[#00e5a0]" :
                    r.status === "failed" ? "bg-[#ff6040]" : "bg-[#f0c040]"
                  }`} />
                  <span className="text-sm text-white group-hover:text-[#b0a0ff] transition-colors">
                    {r.brand}
                  </span>
                </div>
                <span className="text-xs text-[#555]">
                  {new Date(r.created_at).toLocaleDateString(locale === "zh" ? "zh-CN" : "en-US", {
                    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                  })}
                </span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
