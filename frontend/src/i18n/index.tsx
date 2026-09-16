import React, { createContext, useContext, useMemo, useState } from "react";
import { locales, type TranslationKey } from "./locales";
import { getTelegramLanguageCode } from "../telegram";
import type { SupportedLanguage } from "../types";

interface I18nContextValue {
  locale: SupportedLanguage;
  setLocale: (locale: SupportedLanguage) => void;
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

/** Best-effort language before the backend's stored preference has loaded. */
export function detectInitialLocale(): SupportedLanguage {
  const primary = getTelegramLanguageCode()?.split("-")[0];
  if (primary === "ru" || primary === "uk") return primary;
  return "en";
}

export function I18nProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const [locale, setLocale] = useState<SupportedLanguage>(detectInitialLocale());

  const t = useMemo(() => {
    return (key: TranslationKey, vars?: Record<string, string | number>): string => {
      let text = locales[locale][key] ?? locales.en[key] ?? key;
      if (vars) {
        for (const [name, value] of Object.entries(vars)) {
          text = text.replace(`{{${name}}}`, String(value));
        }
      }
      return text;
    };
  }, [locale]);

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}