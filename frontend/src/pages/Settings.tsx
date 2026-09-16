import React, { useState } from "react";
import { Card } from "../components";
import { useAppData } from "../appData";
import { useI18n } from "../i18n";
import { updateLanguage } from "../api";
import { hapticNotification } from "../telegram";
import type { SupportedLanguage } from "../types";

const LANGUAGE_OPTIONS: { code: SupportedLanguage; label: string }[] = [
  { code: "en", label: "🇬🇧 English" },
  { code: "ru", label: "🇷🇺 Русский" },
  { code: "uk", label: "🇺🇦 Українська" },
];

export default function Settings(): React.JSX.Element {
  const { me, loading, error, setMe } = useAppData();
  const { t } = useI18n();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  if (loading) return <div className="screen-state">{t("common.loading")}</div>;
  if (error || !me) return <div className="screen-state">{t("common.error")}</div>;

  async function handleSelect(code: SupportedLanguage) {
    if (code === me!.language || saving) return;
    setSaving(true);
    setSaved(false);
    try {
      const updated = await updateLanguage(code);
      setMe(updated);
      setSaved(true);
      hapticNotification("success");
    } catch {
      hapticNotification("error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="screen">
      <Card>
        <h3>{t("settings.language")}</h3>
        <div className="language-list">
          {LANGUAGE_OPTIONS.map((option) => (
            <button
              key={option.code}
              className={`language-option ${me.language === option.code ? "selected" : ""}`}
              onClick={() => handleSelect(option.code)}
              disabled={saving}
            >
              {option.label}
            </button>
          ))}
        </div>
        {saved && <p className="muted-note">{t("settings.languageSaved")}</p>}
      </Card>
    </div>
  );
}