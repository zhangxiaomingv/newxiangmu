"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslations, useLocale } from "next-intl";
import { startAnalysis } from "@/lib/api";
import LanguageSwitcher from "@/components/LanguageSwitcher";

// ── Scroll-aware nav ──────────────────────────────────

function Nav({ t, locale }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#0a0a1a]/90 backdrop-blur-md border-b border-[#2a2a5a]/50 shadow-lg shadow-black/20"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <span
          className="text-xl font-bold bg-gradient-to-r from-[#7c5cfc] to-[#00e5a0] bg-clip-text text-transparent cursor-pointer"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          ZKONER
        </span>
        <div className="hidden md:flex items-center gap-8">
          {[
            ["product", "productLines"],
            ["howItWorks", "loop"],
            ["pricing", "pricing"],
          ].map(([label, id]) => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className="text-sm text-[#8888aa] hover:text-white transition-colors cursor-pointer"
            >
              {t(`nav.${label}`)}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <LanguageSwitcher />
          <button
            onClick={() => scrollTo("hero")}
            className="hidden md:block px-4 py-2 bg-[#7c5cfc] hover:bg-[#5a3fd4] text-white text-sm font-medium rounded-lg transition-all cursor-pointer"
          >
            {t("nav.startFree")}
          </button>
        </div>
      </div>
    </nav>
  );
}

// ── Section wrapper ───────────────────────────────────

function Section({ id, className = "", children }) {
  return (
    <section id={id} className={`py-24 px-4 ${className}`}>
      <div className="max-w-6xl mx-auto">{children}</div>
    </section>
  );
}

function SectionLabel({ children }) {
  return (
    <p className="text-xs font-semibold tracking-[0.2em] text-[#7c5cfc] uppercase mb-4">
      {children}
    </p>
  );
}

// ── Hero ──────────────────────────────────────────────

function Hero({ t, onSubmit, brand, setBrand, loading, error, locale }) {
  return (
    <Section
      id="hero"
      className="min-h-screen flex items-center justify-center pt-20 relative overflow-hidden"
    >
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-[#7c5cfc]/10 rounded-full blur-[120px]" />
        <div className="absolute top-1/3 left-1/3 w-[300px] h-[300px] bg-[#00e5a0]/8 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-3xl mx-auto text-center relative z-10">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight leading-tight">
          <span className="bg-gradient-to-r from-[#7c5cfc] via-[#a78bfa] to-[#00e5a0] bg-clip-text text-transparent">
            {t("hero.title")}
          </span>
        </h1>
        <p className="text-lg md:text-xl text-[#8888aa] leading-relaxed mb-10 max-w-xl mx-auto">
          {t("hero.subtitle")}
        </p>

        {/* Input form */}
        <form
          onSubmit={onSubmit}
          className="flex flex-col sm:flex-row gap-3 max-w-lg mx-auto"
        >
          <input
            type="text"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder={t("hero.placeholder")}
            className="flex-1 px-5 py-4 bg-[#12122a] border border-[#2a2a5a] rounded-xl text-white placeholder-[#666688] outline-none focus:border-[#7c5cfc] focus:ring-1 focus:ring-[#7c5cfc] transition-all text-base"
            disabled={loading}
            autoFocus
          />
          <button
            type="submit"
            disabled={loading || !brand.trim()}
            className="px-8 py-4 bg-gradient-to-r from-[#7c5cfc] to-[#5a3fd4] text-white rounded-xl font-semibold text-base transition-all hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
          >
            {loading ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {t("hero.analyzing")}
              </>
            ) : (
              t("hero.cta")
            )}
          </button>
        </form>

        {error && (
          <p className="text-[#ff6040] text-sm mt-4 bg-[#ff6040]/10 rounded-lg px-4 py-3 inline-block">
            {error}
          </p>
        )}

        <p className="text-xs text-[#555] mt-6">
          {locale === "zh"
            ? "免费分析一个品牌，无需注册"
            : "Free analysis for one brand · No signup required"}
        </p>
      </div>
    </Section>
  );
}

// ── Problem ───────────────────────────────────────────

function Problem({ t }) {
  return (
    <Section id="problem">
      <SectionLabel>{t("problem.label")}</SectionLabel>
      <h2 className="text-3xl md:text-4xl font-bold mb-6">{t("problem.title")}</h2>
      <p className="text-base text-[#8888aa] leading-relaxed max-w-3xl mb-12">
        {t("problem.description")}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {t.raw("problem.stats").map((stat, i) => (
          <div
            key={i}
            className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 text-center hover:border-[#7c5cfc]/30 transition-all"
          >
            <p className="text-4xl font-bold bg-gradient-to-r from-[#7c5cfc] to-[#00e5a0] bg-clip-text text-transparent mb-2">
              {stat.value}
            </p>
            <p className="text-sm text-[#8888aa]">{stat.label}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

// ── Solution ──────────────────────────────────────────

function Solution({ t }) {
  return (
    <Section>
      <div className="bg-gradient-to-br from-[#7c5cfc]/10 to-[#00e5a0]/10 border border-[#2a2a5a] rounded-3xl p-10 md:p-16 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">{t("solution.title")}</h2>
        <p className="text-base text-[#c0c0d0] leading-relaxed max-w-2xl mx-auto">
          {t("solution.description")}
        </p>
      </div>
    </Section>
  );
}

// ── Product Loop ──────────────────────────────────────

function ProductLoop({ t }) {
  return (
    <Section id="loop">
      <SectionLabel>{t("loop.label")}</SectionLabel>
      <h2 className="text-3xl md:text-4xl font-bold mb-4">{t("loop.title")}</h2>
      <p className="text-base text-[#8888aa] mb-14">{t("loop.subtitle")}</p>

      <div className="relative">
        {/* Connecting line */}
        <div className="hidden md:block absolute top-8 left-0 right-0 h-0.5 bg-gradient-to-r from-[#7c5cfc] via-[#00e5a0] to-[#7c5cfc]" />

        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          {t.raw("loop.steps").map((step, i) => (
            <div key={i} className="relative text-center group">
              <div className="relative z-10 w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[#7c5cfc] to-[#5a3fd4] flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-[#7c5cfc]/20 group-hover:scale-110 transition-transform">
                {i + 1}
              </div>
              <h3 className="text-sm font-semibold text-white mb-1">{step.title}</h3>
              <p className="text-xs text-[#8888aa] leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

// ── Product Lines ─────────────────────────────────────

function ProductLines({ t }) {
  return (
    <Section id="productLines">
      <SectionLabel>{t("productLines.label")}</SectionLabel>
      <h2 className="text-3xl md:text-4xl font-bold mb-12">{t("productLines.title")}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {t.raw("productLines.items").map((item, i) => (
          <div
            key={i}
            className="bg-[#12122a] border border-[#2a2a5a] rounded-2xl p-8 hover:border-[#7c5cfc]/30 transition-all group"
          >
            <span className="text-3xl mb-4 block">{item.icon}</span>
            <h3 className="text-lg font-semibold text-white mb-2">{item.name}</h3>
            <p className="text-sm text-[#8888aa] leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

// ── Dashboard Metrics ─────────────────────────────────

function DashboardMetrics({ t }) {
  return (
    <Section>
      <SectionLabel>{t("dashboard.label")}</SectionLabel>
      <h2 className="text-3xl md:text-4xl font-bold mb-4">{t("dashboard.title")}</h2>
      <p className="text-base text-[#8888aa] mb-12">{t("dashboard.subtitle")}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {t.raw("dashboard.metrics").map((m, i) => (
          <div
            key={i}
            className="bg-[#12122a] border border-[#2a2a5a] rounded-xl p-5 hover:border-[#7c5cfc]/20 transition-all"
          >
            <span className="text-2xl font-bold text-[#7c5cfc]">0{i + 1}</span>
            <h3 className="text-sm font-semibold text-white mt-2 mb-1">{m.name}</h3>
            <p className="text-xs text-[#8888aa] leading-relaxed">{m.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

// ── Pricing ───────────────────────────────────────────

function Pricing({ t, locale }) {
  return (
    <Section id="pricing">
      <SectionLabel>{t("pricing.label")}</SectionLabel>
      <h2 className="text-3xl md:text-4xl font-bold mb-12">{t("pricing.title")}</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {t.raw("pricing.plans").map((plan, i) => (
          <div
            key={i}
            className={`relative rounded-2xl p-6 border transition-all ${
              plan.highlight
                ? "bg-gradient-to-b from-[#7c5cfc]/10 to-transparent border-[#7c5cfc] shadow-lg shadow-[#7c5cfc]/10"
                : "bg-[#12122a] border-[#2a2a5a] hover:border-[#555]"
            }`}
          >
            {plan.highlight && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-semibold bg-[#7c5cfc] text-white px-3 py-1 rounded-full">
                {locale === "zh" ? "推荐" : "Popular"}
              </span>
            )}
            <h3 className="text-lg font-semibold text-white mb-1">{plan.name}</h3>
            <p className="text-xs text-[#8888aa] mb-4">{plan.desc}</p>
            <div className="mb-4">
              <span className="text-3xl font-bold text-white">{plan.price}</span>
              {plan.period && (
                <span className="text-sm text-[#8888aa]">{plan.period}</span>
              )}
            </div>
            <ul className="space-y-2 mb-6">
              {plan.features.map((f, j) => (
                <li key={j} className="flex items-start gap-2 text-sm text-[#c0c0d0]">
                  <span className="text-[#00e5a0] mt-0.5 shrink-0">✓</span>
                  {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => {
                document.getElementById("hero")?.scrollIntoView({ behavior: "smooth" });
              }}
              className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                plan.highlight
                  ? "bg-gradient-to-r from-[#7c5cfc] to-[#5a3fd4] text-white hover:opacity-90"
                  : "bg-[#1a1a3a] text-white border border-[#2a2a5a] hover:border-[#555]"
              }`}
            >
              {plan.cta}
            </button>
          </div>
        ))}
      </div>
    </Section>
  );
}

// ── Final CTA ─────────────────────────────────────────

function FinalCTA({ t, locale }) {
  return (
    <Section>
      <div className="text-center">
        <p className="text-lg text-[#8888aa] mb-2">{t("cta.title")}</p>
        <p className="text-2xl md:text-3xl font-semibold text-[#c0c0d0] mb-2">
          {t("cta.subtitle")}
        </p>
        <p className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-[#7c5cfc] to-[#00e5a0] bg-clip-text text-transparent mb-10">
          {t("cta.highlight")}
        </p>
        <button
          onClick={() => {
            document.getElementById("hero")?.scrollIntoView({ behavior: "smooth" });
          }}
          className="px-10 py-5 bg-gradient-to-r from-[#7c5cfc] to-[#00e5a0] text-white rounded-xl font-bold text-lg transition-all hover:opacity-90 shadow-lg shadow-[#7c5cfc]/25 cursor-pointer"
        >
          {t("cta.button")}
        </button>
      </div>
    </Section>
  );
}

// ── Footer ────────────────────────────────────────────

function Footer({ t }) {
  return (
    <footer className="border-t border-[#2a2a5a] py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <p className="text-lg font-bold bg-gradient-to-r from-[#7c5cfc] to-[#00e5a0] bg-clip-text text-transparent mb-1">
              ZKONER
            </p>
            <p className="text-xs text-[#8888aa]">{t("footer.tagline")}</p>
            <p className="text-xs text-[#555] mt-1">{t("footer.mission")}</p>
          </div>
          <div className="flex gap-8 text-sm text-[#8888aa]">
            <span className="hover:text-white cursor-pointer transition-colors">{t("footer.product")}</span>
            <span className="hover:text-white cursor-pointer transition-colors">{t("footer.pricing")}</span>
            <span className="hover:text-white cursor-pointer transition-colors">{t("footer.vision")}</span>
          </div>
        </div>
        <p className="text-xs text-[#555] text-center mt-10">
          © 2026 ZKONER. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

// ── Main Page ─────────────────────────────────────────

export default function Home() {
  const router = useRouter();
  const t = useTranslations();
  const locale = useLocale();
  const [brand, setBrand] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!brand.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await startAnalysis(brand.trim(), null, locale);
      const prefix = locale === "en" ? "" : `/${locale}`;
      router.push(`${prefix}/analysis/${result.id}`);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a1a] text-[#e8e8f0]">
      <Nav t={t} locale={locale} />
      <Hero
        t={t}
        onSubmit={handleSubmit}
        brand={brand}
        setBrand={setBrand}
        loading={loading}
        error={error}
        locale={locale}
      />
      <Problem t={t} />
      <Solution t={t} />
      <ProductLoop t={t} />
      <ProductLines t={t} />
      <DashboardMetrics t={t} />
      <Pricing t={t} locale={locale} />
      <FinalCTA t={t} locale={locale} />
      <Footer t={t} />
    </div>
  );
}
