import React from "react";
import { NavLink } from "react-router-dom";
import { useI18n } from "../i18n";
import { hapticSelection } from "../telegram";

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}): React.JSX.Element {
  return <div className={`card ${className}`}>{children}</div>;
}

export function ComingSoon({ icon, text }: { icon: string; text: string }): React.JSX.Element {
  const { t } = useI18n();
  return (
    <div className="coming-soon">
      <div className="coming-soon-icon">{icon}</div>
      <div className="coming-soon-badge">{t("common.comingSoon")}</div>
      <p>{text}</p>
    </div>
  );
}

interface NavItem {
  to: string;
  icon: string;
  labelKey: "nav.home" | "nav.balance" | "nav.businesses" | "nav.quests" | "nav.achievements" | "nav.leaderboard" | "nav.profile" | "nav.settings";
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", icon: "🏙️", labelKey: "nav.home" },
  { to: "/balance", icon: "💰", labelKey: "nav.balance" },
  { to: "/businesses", icon: "💼", labelKey: "nav.businesses" },
  { to: "/quests", icon: "🎯", labelKey: "nav.quests" },
  { to: "/achievements", icon: "🏅", labelKey: "nav.achievements" },
  { to: "/leaderboard", icon: "🏆", labelKey: "nav.leaderboard" },
  { to: "/profile", icon: "👤", labelKey: "nav.profile" },
  { to: "/settings", icon: "⚙️", labelKey: "nav.settings" },
];

export function BottomNav(): React.JSX.Element {
  const { t } = useI18n();
  return (
    <nav className="bottom-nav">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === "/"}
          className={({ isActive }) => `bottom-nav-item ${isActive ? "active" : ""}`}
          onClick={hapticSelection}
        >
          <span className="bottom-nav-icon">{item.icon}</span>
          <span className="bottom-nav-label">{t(item.labelKey)}</span>
        </NavLink>
      ))}
    </nav>
  );
}