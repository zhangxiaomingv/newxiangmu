"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "next/navigation";
import { useTransition } from "react";

export default function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();

  function switchLocale(nextLocale) {
    if (nextLocale === locale) return;
    startTransition(() => {
      // Strip current locale prefix from path
      let newPath = pathname;
      if (locale !== "en") {
        newPath = newPath.replace(`/${locale}`, "") || "/";
      }

      // Add new locale prefix if not English
      if (nextLocale !== "en") {
        newPath = `/${nextLocale}${newPath}`;
      }

      router.replace(newPath);
      router.refresh();
    });
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
          disabled={isPending}
          className={`px-3 py-1 text-xs rounded-md transition-all font-medium ${
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
