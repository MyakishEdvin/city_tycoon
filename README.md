# CITY TYCOON

A Telegram-native economic simulation game: businesses, districts, companies,
groups, events, and a Mini App city view. Built incrementally, phase by phase.

**Phase 1 (this snapshot):** Telegram bot, PostgreSQL, user registration,
profile, referral wiring, and the full menu (with placeholders for features
that land in later phases).

---

## 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Create a Telegram bot with BotFather

1. Open Telegram, message **@BotFather**.
2. Send `/newbot`, choose a name and a unique username ending in `bot`.
3. Copy the token BotFather gives you (looks like `123456789:AA...`).

## 3. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```
BOT_TOKEN=<the token from BotFather>
DATABASE_URL=postgresql+asyncpg://city_tycoon:city_tycoon@localhost:5432/city_tycoon
REDIS_URL=redis://localhost:6379/0
WEBAPP_URL=
SECRET_KEY=<generate one, e.g. `python -c "import secrets;print(secrets.token_hex(32))"`>
ENVIRONMENT=development
```

Leave `WEBAPP_URL` empty until Phase 3 (Mini App) is deployed — the
"🏙️ OPEN CITY" button gracefully falls back to a text button until then.

## 4. Configure PostgreSQL

**Option A — Docker (recommended for local dev):**

```bash
docker compose up -d postgres redis
```

This starts Postgres on `localhost:5432` with the credentials already
matching `.env.example` (`city_tycoon` / `city_tycoon` / db `city_tycoon`).

**Option B — existing local Postgres:**

Create a database and user matching whatever you put in `DATABASE_URL`:

```sql
CREATE USER city_tycoon WITH PASSWORD 'city_tycoon';
CREATE DATABASE city_tycoon OWNER city_tycoon;
```

## 5. Configure Redis

Not used yet in Phase 1 (rate limiting/caching arrive in later phases), but
it's already wired into `.env` and `docker-compose.yml` so nothing needs to
change when it's needed. `docker compose up -d redis` starts it locally.

## 6. Run Alembic migrations

```bash
alembic upgrade head
```

This creates the `users` table. To generate a new migration after changing
a model in a later phase:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## 7. Start the bot

```bash
python -m bot.main
```

You should see a `Starting CITY TYCOON bot` log line. Message your bot on
Telegram with `/start` — it should register you, show your starting
$1,000 balance, and display the main menu.

## 8. Start the backend

Not introduced yet — the FastAPI backend arrives in Phase 3 alongside the
Mini App.

## 9. Build the Mini App

Not introduced yet — arrives in Phase 3.

## 10. Connect the Mini App to Telegram

Not introduced yet — arrives in Phase 3, once `WEBAPP_URL` points at a real
deployed HTTPS frontend.

## 11. Deploy to Render / Railway / a VPS

Deployment instructions will be expanded in Phase 10 once the backend,
Mini App, and Docker setup for all services exist. For now, the bot alone
can run anywhere that can reach your Postgres instance and has network
access to `api.telegram.org` — set the same `.env` values as above.

## 12. Run tests

```bash
pytest
```

Tests use an isolated in-memory SQLite database per test (via `aiosqlite`)
so they never touch your real Postgres instance. Covered in Phase 1:
user registration, idempotent `/start`, referral linking.

> **Note on this sandbox:** these files were written and syntax-checked in
> an offline sandbox with no package registry access, so `pytest` and
> `python -m bot.main` weren't executed here end-to-end. Run the steps
> above in your own environment to install real dependencies and confirm
> the full suite passes.

---

## Project structure (Phase 1)

```
city_tycoon/
├── bot/
│   ├── config.py            # typed Settings (pydantic-settings)
│   ├── main.py              # entrypoint: dispatcher + routers
│   ├── handlers/
│   │   ├── start.py         # /start — registration, referrals
│   │   ├── profile.py       # /profile, Balance button
│   │   └── common.py        # /help, /settings, placeholders for later phases
│   ├── keyboards/
│   │   └── main_menu.py     # main reply keyboard + OPEN CITY button
│   └── middlewares/
│       └── database.py      # injects one AsyncSession per update
├── database/
│   ├── database.py          # async engine, session factory, Base
│   ├── models/
│   │   ├── user.py          # User ORM model
│   │   └── user_service.py  # UserService — only writer of the users table
│   └── migrations/          # Alembic (async-engine env.py)
├── game/                    # empty — economy/businesses/quests land in Phase 2+
├── tests/
├── requirements.txt
├── .env.example
├── alembic.ini
├── docker-compose.yml       # postgres + redis (+ bot, once you set BOT_TOKEN)
├── Dockerfile
└── README.md
```

## Core economy (this update)

Added on top of Phase 1, in the existing project structure:

* **`game/economy.py`** — centralized economy config: `STARTING_BALANCE`,
  `DistrictID`/`DISTRICT_DISPLAY_NAMES`, `TransactionType`, and
  `InsufficientFundsError`. `database/models/user.py` now imports its
  constants from here instead of defining them locally.
* **`database/models/transaction.py`** — `Transaction` model: append-only
  audit log (`amount`, `balance_before`, `balance_after`, `reference_id`,
  `created_at`), with a unique constraint on `reference_id` for
  idempotency.
* **`database/models/transaction_service.py`** — `TransactionService`,
  the only code path allowed to change `User.money`. `apply_delta(...)`
  locks the user row (`SELECT ... FOR UPDATE`), rejects any change that
  would take the balance below zero, writes the balance update and the
  audit row in one atomic commit, and is idempotent when a
  `reference_id` is supplied — a duplicate call returns the original
  transaction instead of applying the change twice.
* **`database/models/city.py`** — `PlayerCity`: minimal city ownership
  data (`unlocked_districts`), one row per user, created automatically
  at registration.
* **`database/models/city_service.py`** — read-only `CityService` for
  fetching a user's city and mapping district ids to display names.
* **`database/models/user_service.py`** — `get_or_create` now also
  creates a user's starting `PlayerCity` and a `STARTING_BALANCE`
  transaction row in the *same* commit as the new `User` row, so
  registration is a single atomic unit.
* **Migration `0002_add_transactions_and_city.py`** — adds the
  `transactions` and `player_cities` tables (no changes to `users`).
* **Bot handlers**: `/city` now shows real owned districts;
  `💰 Balance` shows the balance plus the 5 most recent transactions;
  new `/transactions` command shows the last 20.
* **Tests**: `tests/test_economy.py` covers starting-balance creation,
  credit/debit, insufficient-funds rejection, idempotent duplicate
  transactions, the DB-level uniqueness backstop, and history ordering.

### Run the migration and tests

```bash
alembic upgrade head
pytest
```

> Same sandbox caveat as Phase 1: these files were written and
> syntax-checked (`python -m py_compile`) offline with no package
> registry access, so `pytest`, `alembic upgrade head`, and
> `python -m bot.main` weren't executed end-to-end here. Run them in
> your own environment as the first check after pulling this update.

## What's next (businesses)

Business types, purchases, upgrades, income accrual, and offline income
calculated from timestamps (not a background loop per user) — building
directly on `TransactionService` for every money movement.
