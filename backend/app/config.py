from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

load_dotenv(ROOT / ".env")


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    app_name = "Bocat World Cup"
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    timezone = "Africa/Johannesburg"
    live_state_path = Path(os.getenv("LIVE_STATE_PATH", str(DATA_DIR / "live_state.json"))).expanduser()
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,https://bocatworldcup.netlify.app",
        ).split(",")
        if origin.strip()
    ]
    live_matches_api_url = os.getenv("LIVE_MATCHES_API_URL", "").strip()
    live_matches_api_key = os.getenv("LIVE_MATCHES_API_KEY", "").strip()
    live_matches_api_key_header = os.getenv("LIVE_MATCHES_API_KEY_HEADER", "x-apisports-key").strip()
    live_matches_extra_headers = os.getenv("LIVE_MATCHES_EXTRA_HEADERS", "").strip()
    live_matches_provider = os.getenv("LIVE_MATCHES_PROVIDER", "generic").strip().lower()
    fallback_scores_provider = os.getenv("FALLBACK_SCORES_PROVIDER", "espn").strip().lower()
    fallback_scores_url_template = os.getenv(
        "FALLBACK_SCORES_URL_TEMPLATE",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={date}",
    ).strip()
    qualification_standings_url = os.getenv(
        "QUALIFICATION_STANDINGS_URL",
        "https://site.web.api.espn.com/apis/v2/sports/soccer/fifa.world/standings?season=2026",
    ).strip()
    post_match_delay_minutes = env_int("POST_MATCH_DELAY_MINUTES", 120)
    score_poll_start_minutes_before_kickoff = env_int("SCORE_POLL_START_MINUTES_BEFORE_KICKOFF", 0)
    score_poll_end_minutes_after_kickoff = env_int("SCORE_POLL_END_MINUTES_AFTER_KICKOFF", 180)
    score_poll_interval_minutes = env_int("SCORE_POLL_INTERVAL_MINUTES", 10)
    enable_score_polling = env_bool("ENABLE_SCORE_POLLING", True)
    daily_standings_sync_time = os.getenv("DAILY_STANDINGS_SYNC_TIME", "08:00").strip()
    enable_daily_standings_sync = env_bool("ENABLE_DAILY_STANDINGS_SYNC", True)


settings = Settings()
