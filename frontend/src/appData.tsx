import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { fetchMe } from "./api";
import type { MeResponse } from "./types";
import { useI18n } from "./i18n";

interface AppDataContextValue {
  me: MeResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  setMe: (me: MeResponse) => void;
}

const AppDataContext = createContext<AppDataContextValue | null>(null);

export function AppDataProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const [me, setMeState] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { setLocale } = useI18n();

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMe();
      setMeState(data);
      // The backend-stored preference wins over the Telegram-detected
      // default used before this resolves.
      setLocale(data.language);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [setLocale]);

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setMe = useCallback((data: MeResponse) => {
    setMeState(data);
    setLocale(data.language);
  }, [setLocale]);

  return (
    <AppDataContext.Provider value={{ me, loading, error, refresh, setMe }}>
      {children}
    </AppDataContext.Provider>
  );
}

export function useAppData(): AppDataContextValue {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData must be used within AppDataProvider");
  return ctx;
}