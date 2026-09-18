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
from dataclasses import dataclass

# --- Player starting state ---
STARTING_BALANCE = 1_000
STARTING_ENERGY = 100
STARTING_POPULATION = 1


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
    BUILDING_PURCHASE = "building_purchase"
    BUILDING_UPGRADE = "building_upgrade"
    BUILDING_INCOME = "building_income"


class InsufficientFundsError(Exception):
    """Raised when a debit would take a user's balance below zero."""

    def __init__(self, user_id: int, balance: int, requested: int) -> None:
        self.user_id = user_id
        self.balance = balance
        self.requested = requested
        super().__init__(
            f"User {user_id} has {balance} but the operation requires {requested}"
        )


# =============================================================================
# Buildings (Phase 2)
# =============================================================================


class BuildingType(str, enum.Enum):
    HOUSE = "house"
    SHOP = "shop"
    FACTORY = "factory"


@dataclass(frozen=True)
class BuildingSpec:
    type: BuildingType
    name: str
    description: str
    base_cost: int
    base_income_per_hour: int
    # Population is granted once, at construction — upgrades affect income
    # only. Keeps the model simple for this first playable slice.
    population_bonus: int
    max_level: int
    required_player_level: int
    upgrade_cost_multiplier: float
    income_growth_per_level: float


# Deliberately front-loaded for a fast, satisfying early game: a House is
# affordable with the starting balance, so a new player's very first
# session already includes a build.
BUILDING_CATALOG: dict[BuildingType, BuildingSpec] = {
    BuildingType.HOUSE: BuildingSpec(
        type=BuildingType.HOUSE,
        name="Жилой дом",
        description="Увеличивает население города и приносит небольшой доход",
        base_cost=300,
        base_income_per_hour=10,
        population_bonus=50,
        max_level=5,
        required_player_level=1,
        upgrade_cost_multiplier=1.6,
        income_growth_per_level=1.3,
    ),
    BuildingType.SHOP: BuildingSpec(
        type=BuildingType.SHOP,
        name="Магазин",
        description="Приносит стабильный доход от торговли",
        base_cost=1500,
        base_income_per_hour=60,
        population_bonus=10,
        max_level=5,
        required_player_level=2,
        upgrade_cost_multiplier=1.7,
        income_growth_per_level=1.35,
    ),
    BuildingType.FACTORY: BuildingSpec(
        type=BuildingType.FACTORY,
        name="Фабрика",
        description="Даёт высокий доход, но требует развитого города",
        base_cost=5000,
        base_income_per_hour=200,
        population_bonus=20,
        max_level=5,
        required_player_level=3,
        upgrade_cost_multiplier=1.8,
        income_growth_per_level=1.4,
    ),
}


def building_cost_for_level(spec: BuildingSpec, target_level: int) -> int:
    """
    Cost to reach `target_level`: the construction cost (target_level=1)
    or the upgrade cost to go from `target_level - 1` to `target_level`.
    """
    if target_level <= 1:
        return spec.base_cost
    return round(spec.base_cost * (spec.upgrade_cost_multiplier ** (target_level - 1)))


def building_income_for_level(spec: BuildingSpec, level: int) -> int:
    """Income/hour a building generates at `level`."""
    return round(spec.base_income_per_hour * (spec.income_growth_per_level ** (level - 1)))


# --- Passive income ---
# Caps accumulated offline income so a player can't return after weeks
# away and collect unlimited money — see EconomyService.collect_income.
MAX_OFFLINE_INCOME_HOURS = 8

# --- XP rewards for building actions (granted via ProgressionService) ---
BUILD_XP_REWARD = 50
UPGRADE_XP_REWARD = 30


class InvalidBuildingTypeError(Exception):
    def __init__(self, building_type: str) -> None:
        self.building_type = building_type
        super().__init__(f"Unknown building type: {building_type}")


class BuildingLockedError(Exception):
    """Player's level is below the building's required_player_level."""

    def __init__(self, building_type: str, required_level: int, player_level: int) -> None:
        self.building_type = building_type
        self.required_level = required_level
        self.player_level = player_level
        super().__init__(
            f"{building_type} requires level {required_level}, player is level {player_level}"
        )


class BuildingMaxLevelError(Exception):
    def __init__(self, building_type: str, max_level: int) -> None:
        self.building_type = building_type
        self.max_level = max_level
        super().__init__(f"{building_type} is already at max level {max_level}")


class BuildingNotFoundError(Exception):
    def __init__(self, building_id: int) -> None:
        self.building_id = building_id
        super().__init__(f"Building {building_id} not found")


class BuildingAlreadyExistsError(Exception):
    """A city may only have one building of each type — upgrade it instead."""

    def __init__(self, building_type: str) -> None:
        self.building_type = building_type
        super().__init__(f"{building_type} already exists in this city")