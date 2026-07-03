"use client";

import { useLocale } from "next-intl";
import { usePathname } from "next/navigation";

export default function LanguageSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();

  function switchLocale(nextLocale) {
    if (nextLocale === locale) return;

    // Build the new URL path
    // usePathname() in next-intl already strips the locale prefix
    let newPath = pathname;

    if (nextLocale !== "en") {
      newPath = `/${nextLocale}${newPath === "/" ? "" : newPath}`;
    }

    // Hard navigation ensures a full page reload with the new locale
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
