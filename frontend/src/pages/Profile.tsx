import React from "react";
import { Card } from "../components";
import { useAppData } from "../appData";
import { useI18n } from "../i18n";

export default function Profile(): React.JSX.Element {
  const { me, loading, error } = useAppData();
  const { t } = useI18n();

  if (loading) return <div className="screen-state">{t("common.loading")}</div>;
  if (error || !me) return <div className="screen-state">{t("common.error")}</div>;

  const displayName = me.username ? `@${me.username}` : me.first_name ?? "Tycoon";

  return (
    <div className="screen">
      <div className="hero-card">
        <div className="hero-avatar">👤</div>
        <div className="hero-value">{displayName}</div>
      </div>

      <Card>
        <div className="stat-row">
          <span>{t("profile.level")}</span>
          <span>{me.level}</span>
        </div>
        <div className="stat-row">
          <span>{t("profile.xp")}</span>
          <span>{me.xp}</span>
        </div>
        <div className="stat-row">
          <span>{t("profile.reputation")}</span>
          <span>{me.reputation}</span>
        </div>
        <div className="stat-row">
          <span>{t("profile.energy")}</span>
          <span>{me.energy}</span>
        </div>
        <div className="stat-row">
          <span>{t("profile.streak")}</span>
          <span>{t("profile.streakDays", { count: me.daily_streak })}</span>
        </div>
      </Card>

      <Card>
        <div className="stat-row">
          <span>{t("profile.referralCode")}</span>
          <code>{me.referral_code}</code>
        </div>
      </Card>
    </div>
  );
}