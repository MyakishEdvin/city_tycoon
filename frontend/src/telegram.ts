// Thin wrapper around window.Telegram.WebApp. Every Mini App screen goes
// through here instead of touching window.Telegram directly, so the SDK
// surface we depend on is defined in exactly one place.

export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

export interface TelegramWebAppUser {
  id: number;
  username?: string;
  first_name?: string;
  language_code?: string;
}

export interface TelegramBackButton {
  isVisible: boolean;
  show: () => void;
  hide: () => void;
  onClick: (cb: () => void) => void;
  offClick: (cb: () => void) => void;
}

export interface TelegramMainButton {
  text: string;
  isVisible: boolean;
  show: () => void;
  hide: () => void;
  setText: (text: string) => void;
  onClick: (cb: () => void) => void;
  offClick: (cb: () => void) => void;
  enable: () => void;
  disable: () => void;
}

export interface TelegramHapticFeedback {
  impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
  notificationOccurred: (type: "error" | "success" | "warning") => void;
  selectionChanged: () => void;
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: { user?: TelegramWebAppUser };
  colorScheme: "light" | "dark";
  themeParams: TelegramThemeParams;
  safeAreaInset?: { top: number; bottom: number; left: number; right: number };
  ready: () => void;
  expand: () => void;
  close: () => void;
  BackButton: TelegramBackButton;
  MainButton: TelegramMainButton;
  HapticFeedback: TelegramHapticFeedback;
}

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp };
  }
}

export function getTelegramWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

/** Call once on app start: signals readiness and expands to full height. */
export function initTelegramApp(): void {
  const tg = getTelegramWebApp();
  if (!tg) return;
  tg.ready();
  tg.expand();
  applyThemeVariables(tg.themeParams);
}

export function getInitData(): string {
  return getTelegramWebApp()?.initData ?? "";
}

export function getTelegramLanguageCode(): string | undefined {
  return getTelegramWebApp()?.initDataUnsafe?.user?.language_code;
}

/** Maps Telegram's theme colors onto CSS variables our stylesheet uses. */
function applyThemeVariables(theme: TelegramThemeParams): void {
  const root = document.documentElement.style;
  if (theme.bg_color) root.setProperty("--tg-bg", theme.bg_color);
  if (theme.text_color) root.setProperty("--tg-text", theme.text_color);
  if (theme.hint_color) root.setProperty("--tg-hint", theme.hint_color);
  if (theme.button_color) root.setProperty("--tg-accent", theme.button_color);
  if (theme.secondary_bg_color) root.setProperty("--tg-card-bg", theme.secondary_bg_color);
}

export function hapticSelection(): void {
  getTelegramWebApp()?.HapticFeedback.selectionChanged();
}

export function hapticImpact(style: "light" | "medium" | "heavy" = "light"): void {
  getTelegramWebApp()?.HapticFeedback.impactOccurred(style);
}

export function hapticNotification(type: "error" | "success" | "warning"): void {
  getTelegramWebApp()?.HapticFeedback.notificationOccurred(type);
}

/** Shows the Telegram BackButton and wires it to `onBack`; returns a cleanup fn. */
export function useBackButtonHandler(tg: TelegramWebApp | null, onBack: () => void): () => void {
  if (!tg) return () => {};
  tg.BackButton.show();
  tg.BackButton.onClick(onBack);
  return () => {
    tg.BackButton.offClick(onBack);
    tg.BackButton.hide();
  };
}