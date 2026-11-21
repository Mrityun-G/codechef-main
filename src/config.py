from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    gemini_api_key: str
    codechef_session: str
    codechef_username: str
    model_names: tuple[str, ...]
    dry_run: bool
    daily_target: int
    min_rating: int
    max_rating: int
    rating_step: int
    max_attempts: int
    preferred_language: str

    @classmethod
    def from_env(cls) -> "Config":
        models = tuple(
            item.strip()
            for item in os.getenv("GEMINI_MODELS", "gemini-3.8-flash").split(",")
            if item.strip()
        )
        config = cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            codechef_session=os.getenv("CODECHEF_SESSION", "").strip(),
            codechef_username=os.getenv("CODECHEF_USERNAME", "").strip(),
            model_names=models,
            dry_run=os.getenv("DRY_RUN", "true").strip().lower() in {"1", "true", "yes"},
            daily_target=int(os.getenv("DAILY_TARGET", "5")),
            min_rating=int(os.getenv("MIN_RATING", "200")),
            max_rating=int(os.getenv("MAX_RATING", "1400")),
            rating_step=int(os.getenv("RATING_STEP", "100")),
            max_attempts=int(os.getenv("MAX_ATTEMPTS", "3")),
            preferred_language=os.getenv("SOLUTION_LANGUAGE", "cpp").strip().lower(),
        )
        if not config.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required")
        if not config.codechef_username:
            raise ValueError("CODECHEF_USERNAME is required")
        if not config.dry_run and not config.codechef_session:
            raise ValueError("CODECHEF_SESSION is required when DRY_RUN is false")
        if not config.model_names:
            raise ValueError("GEMINI_MODELS must contain at least one model name")
        if not 1 <= config.daily_target <= 8:
            raise ValueError("DAILY_TARGET must be between 1 and 8")
        if config.min_rating < 0 or config.max_rating < config.min_rating:
            raise ValueError("Rating bounds are invalid")
        if config.max_attempts < 1:
            raise ValueError("MAX_ATTEMPTS must be at least 1")
        if config.preferred_language not in {"cpp", "python"}:
            raise ValueError("SOLUTION_LANGUAGE must be cpp or python")
        return config
