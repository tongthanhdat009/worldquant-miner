from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class PolymarketCredentials:
    api_key: str | None = None
    api_secret: str | None = None
    api_passphrase: str | None = None
    private_key: str | None = None
    funder: str | None = None

    def has_any(self) -> bool:
        return any(
            [
                self.api_key,
                self.api_secret,
                self.api_passphrase,
                self.private_key,
                self.funder,
            ]
        )


def load_polymarket_credentials(credentials_path: str) -> PolymarketCredentials | None:
    """
    Load credentials from environment or file.
    Environment variable takes precedence over file-based value.
    """
    env_credentials = PolymarketCredentials(
        api_key=_read_env("POLYMARKET_API_KEY"),
        api_secret=_read_env("POLYMARKET_API_SECRET"),
        api_passphrase=_read_env("POLYMARKET_API_PASSPHRASE"),
        private_key=_read_env("POLYMARKET_PRIVATE_KEY"),
        funder=_read_env("POLYMARKET_FUNDER"),
    )
    if env_credentials.has_any():
        return env_credentials

    path = Path(credentials_path)
    if not path.exists():
        return None

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return None

    # Accept either plain token or key=value format.
    if "=" in content:
        parsed: dict[str, str] = {}
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            parsed[key.strip().upper()] = value.strip()
        credentials = PolymarketCredentials(
            api_key=parsed.get("POLYMARKET_API_KEY") or parsed.get("API_KEY"),
            api_secret=parsed.get("POLYMARKET_API_SECRET") or parsed.get("API_SECRET"),
            api_passphrase=parsed.get("POLYMARKET_API_PASSPHRASE")
            or parsed.get("API_PASSPHRASE"),
            private_key=parsed.get("POLYMARKET_PRIVATE_KEY")
            or parsed.get("PRIVATE_KEY"),
            funder=parsed.get("POLYMARKET_FUNDER") or parsed.get("FUNDER"),
        )
        if credentials.has_any():
            return credentials
    else:
        return PolymarketCredentials(api_key=content)

    return None


def _read_env(key: str) -> str | None:
    value = os.getenv(key)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None

