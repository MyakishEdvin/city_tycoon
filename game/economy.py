"""
Centralized economy configuration.

Per the project spec, all tunable economic values, enums, and progression
constants live here rather than being scattered/hard-coded across models
and handlers. Phase 2+ (businesses, quests, marketplace, ...) will keep
extending this module (upgrade cost curves, income formulas, fee rates)
rather than defining their own scattered constants.
"""

from __future__ import annotations

import enum

# --- Player starting state ---
STARTING_BALANCE = 1_000
STARTING_ENERGY = 100


class DistrictID(str, enum.Enum):
    """
    The seven districts from the game design doc. Only OLD_TOWN is
    unlocked at registration; unlock rules based on level/reputation/
    capital for the others arrive alongside the business/city system.
    """

    OLD_TOWN = "old_town"
    CITY_CENTER = "city_center"
    BUSINESS_DISTRICT = "business_district"
    INDUSTRIAL_ZONE = "industrial_zone"
    HARBOR = "harbor"
    RICH_DISTRICT = "rich_district"
    TECHNOLOGY_DISTRICT = "technology_district"


DISTRICT_DISPLAY_NAMES: dict[DistrictID, str] = {
    DistrictID.OLD_TOWN: "Old Town",
    DistrictID.CITY_CENTER: "City Center",
    DistrictID.BUSINESS_DISTRICT: "Business District",
    DistrictID.INDUSTRIAL_ZONE: "Industrial Zone",
    DistrictID.HARBOR: "Harbor",
    DistrictID.RICH_DISTRICT: "Rich District",
    DistrictID.TECHNOLOGY_DISTRICT: "Technology District",
}

# Districts a brand-new player owns immediately. Stored as plain strings
# (DistrictID.value) since that's how they're persisted in PlayerCity.
DEFAULT_UNLOCKED_DISTRICTS: list[str] = [DistrictID.OLD_TOWN.value]


class TransactionType(str, enum.Enum):
    """
    Every reason a user's balance can change. Stored on Transaction.type
    as plain text (not a native SQL enum) so future phases can add new
    values without an ALTER TYPE migration — only this enum needs a new
    member, plus a normal Python code change.

    New members are added here as each subsystem is built:
    businesses (BUSINESS_INCOME, BUSINESS_PURCHASE, BUSINESS_UPGRADE),
    quests (QUEST_REWARD), daily rewards (DAILY_REWARD), marketplace
    (MARKETPLACE_SALE, MARKETPLACE_PURCHASE), referrals
    (REFERRAL_BONUS), events (EVENT_REWARD), and so on.
    """

    STARTING_BALANCE = "starting_balance"
    ADMIN_CREDIT = "admin_credit"
    ADMIN_DEBIT = "admin_debit"


class InsufficientFundsError(Exception):
    """Raised when a debit would take a user's balance below zero."""

    def __init__(self, user_id: int, balance: int, requested: int) -> None:
        self.user_id = user_id
        self.balance = balance
        self.requested = requested
        super().__init__(
            f"User {user_id} has {balance} but the operation requires {requested}"
        )
