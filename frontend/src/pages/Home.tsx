import React from "react";
import { Card } from "../components";
import { useAppData } from "../appData";
import { useI18n } from "../i18n";

const DISTRICT_ICONS: Record<string, string> = {
  old_town: "🏘️",
  city_center: "🏢",
  business_district: "💼",
  industrial_zone: "🏭",
  harbor: "⚓",
  rich_district: "🏰",
  technology_district: "🖥️",
};

export default function Home(): React.JSX.Element {
  const { me, loading, error } = useAppData();
  const { t } = useI18n();

  if (loading) return <div className="screen-state">{t("common.loading")}</div>;
  if (error || !me) return <div className="screen-state">{t("common.error")}</div>;

  return (
    <div className="screen">
      <div className="hero-card">
        <div className="hero-label">{t("home.balance")}</div>
        <div className="hero-value">${me.money.toLocaleString()}</div>
        <div className="hero-sub">
          {t("home.level")} {me.level}
        </div>
        <div className="xp-bar">
          <div
            className="xp-bar-fill"
            style={{ width: `${Math.round(me.level_progress * 100)}%` }}
          />
        </div>
        <div className="hero-sub">
          {me.xp} / {me.xp_for_next_level} XP
        </div>
      </div>

      <Card>
        <div className="stat-row">
          <span>{t("home.population")}</span>
          <span>{me.city.population.toLocaleString()}</span>
        </div>
        <div className="stat-row">
          <span>{t("home.buildings")}</span>
          <span>{me.city.building_count}</span>
        </div>
      </Card>

      <Card>
        <h3>{t("home.districtsOwned")} ({me.city.unlocked_districts.length})</h3>
        <div className="district-grid">
          {me.city.unlocked_districts.map((district) => (
            <div key={district} className="district-tile">
              <span className="district-icon">{DISTRICT_ICONS[district] ?? "🏙️"}</span>
              <span>{district.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
      </Card>

      <p className="muted-note">{t("home.buildingsComingSoon")}</p>
    </div>
  );
}