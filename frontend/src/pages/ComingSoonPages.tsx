import React from "react";
import { ComingSoon } from "../components";
import { useI18n } from "../i18n";

export function BusinessesPage(): React.JSX.Element {
  const { t } = useI18n();
  return (
    <div className="screen">
      <ComingSoon icon="💼" text={t("comingSoon.businesses")} />
    </div>
  );
}

export function BusinessDetailPage(): React.JSX.Element {
  const { t } = useI18n();
  return (
    <div className="screen">
      <ComingSoon icon="🏪" text={t("comingSoon.businessDetail")} />
    </div>
  );
}

export function UpgradesPage(): React.JSX.Element {
  const { t } = useI18n();
  return (
    <div className="screen">
      <ComingSoon icon="⬆️" text={t("comingSoon.upgrades")} />
    </div>
  );
}

export function QuestsPage(): React.JSX.Element {
  const { t } = useI18n();
  return (
    <div className="screen">
      <ComingSoon icon="🎯" text={t("comingSoon.quests")} />
    </div>
  );
}

export function AchievementsPage(): React.JSX.Element {
  const { t } = useI18n();
  return (
    <div className="screen">
      <ComingSoon icon="🏅" text={t("comingSoon.achievements")} />
    </div>
  );
}

export function LeaderboardPage(): React.JSX.Element {
  const { t } = useI18n();
  return (
    <div className="screen">
      <ComingSoon icon="🏆" text={t("comingSoon.leaderboard")} />
    </div>
  );
}