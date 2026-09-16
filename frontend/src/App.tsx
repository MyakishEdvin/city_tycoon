import React, { useEffect } from "react";
import { Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { BottomNav } from "./components";
import { AppDataProvider } from "./appData";
import { getTelegramWebApp, useBackButtonHandler } from "./telegram";
import Home from "./pages/Home";
import Balance from "./pages/Balance";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import {
  BusinessesPage,
  BusinessDetailPage,
  UpgradesPage,
  QuestsPage,
  AchievementsPage,
  LeaderboardPage,
} from "./pages/ComingSoonPages";

function BackButtonController(): null {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const tg = getTelegramWebApp();
    if (!tg) return;
    if (location.pathname === "/") {
      tg.BackButton.hide();
      return;
    }
    return useBackButtonHandler(tg, () => navigate(-1));
  }, [location.pathname, navigate]);

  return null;
}

export default function App(): React.JSX.Element {
  return (
    <AppDataProvider>
      <div className="app-shell">
        <BackButtonController />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/balance" element={<Balance />} />
          <Route path="/businesses" element={<BusinessesPage />} />
          <Route path="/businesses/:id" element={<BusinessDetailPage />} />
          <Route path="/upgrades" element={<UpgradesPage />} />
          <Route path="/quests" element={<QuestsPage />} />
          <Route path="/achievements" element={<AchievementsPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <BottomNav />
      </div>
    </AppDataProvider>
  );
}