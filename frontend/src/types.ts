export interface CityOut {
  unlocked_districts: string[];
  population: number;
  building_count: number;
}

export interface MeResponse {
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  level: number;
  xp: number;
  xp_for_next_level: number;
  level_progress: number;
  money: number;
  reputation: number;
  energy: number;
  daily_streak: number;
  language: SupportedLanguage;
  referral_code: string;
  city: CityOut;
}

export interface TransactionOut {
  id: number;
  type: string;
  amount: number;
  balance_before: number;
  balance_after: number;
  reference_id: string | null;
  created_at: string;
}

export interface TransactionHistoryResponse {
  items: TransactionOut[];
  limit: number;
  offset: number;
}

export type SupportedLanguage = "en" | "ru" | "uk";