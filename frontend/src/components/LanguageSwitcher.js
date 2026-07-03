"use client";

import { useLocale } from "next-intl";
import { usePathname } from "next/navigation";

export default function LanguageSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();

  function switchLocale(nextLocale) {
    if (nextLocale === locale) return;

    // Strip current locale prefix from pathname
    let newPath = pathname;
    if (locale !== "en") {
      newPath = newPath.replace(`/${locale}`, "") || "/";
    }

    // Set cookie so middleware respects the manual choice
    // (prevents bounce-back from browser language detection)
    document.cookie = `NEXT_LOCALE=${nextLocale}; path=/; max-age=31536000; SameSite=Lax`;

    // Add new locale prefix (default locale "en" has no prefix)
    if (nextLocale !== "en") {
      newPath = `/${nextLocale}${newPath === "/" ? "" : newPath}`;
    }

    window.location.href = newPath;
  }

  const languages = [
    { code: "en", label: "EN" },
    { code: "zh", label: "中文" },
  ];

  return (
    <div className="flex items-center gap-1 bg-[#12122a] border border-[#2a2a5a] rounded-lg p-1">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => switchLocale(lang.code)}
          className={`px-3 py-1 text-xs rounded-md transition-all font-medium cursor-pointer ${
            locale === lang.code
              ? "bg-[#7c5cfc] text-white"
              : "text-[#8888aa] hover:text-white hover:bg-[#1a1a3a]"
          }`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
