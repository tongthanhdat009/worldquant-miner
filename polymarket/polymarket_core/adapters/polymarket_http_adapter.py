import json
from urllib import request
from urllib.error import HTTPError

from .market_adapter import MarketDataAdapter, MarketSnapshot


class PolymarketHTTPAdapter(MarketDataAdapter):
    """
    Real adapter backed by Polymarket's public gamma API.
    If an API key is available, it is attached as a bearer token.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        api_passphrase: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase

    def fetch_markets(self) -> list[MarketSnapshot]:
        rows = self._fetch_all_market_rows()
        snapshots: list[MarketSnapshot] = []
        for row in rows:
            if row.get("enableOrderBook") is False:
                continue
            expiration_iso = str(row.get("endDateIso") or row.get("endDate") or "").strip()
            # Enforce real market lifecycle data: skip markets without expiration.
            if not expiration_iso:
                continue
            cashout_iso = str(row.get("endDateIso") or row.get("endDate") or "").strip()
            market_id = str(
                row.get("id")
                or row.get("market_slug")
                or row.get("slug")
                or row.get("questionID")
                or "unknown-market"
            )
            question = str(row.get("question") or row.get("title") or market_id)
            event_title = _extract_event_title(row)
            category = _classify_market_category(question=question, event_title=event_title)
            probability = _as_float(
                row.get("probability")
                or row.get("lastTradePrice")
                or row.get("outcomePrice")
                or 0.5
            )
            token_ids = _parse_json_list(row.get("clobTokenIds"))
            outcome_prices = _parse_json_list(row.get("outcomePrices"))
            yes_token_id = str(token_ids[0]) if token_ids else market_id
            yes_price = _as_float(outcome_prices[0] if outcome_prices else probability)
            liquidity = _as_float(row.get("liquidity") or row.get("liquidityNum") or 0.0)
            volume_24h = _as_float(
                row.get("volume24hr") or row.get("volume24h") or row.get("volumeNum") or 0.0
            )
            one_hour_price_change = _as_float(row.get("oneHourPriceChange") or 0.0)
            one_week_price_change = _as_float(row.get("oneWeekPriceChange") or 0.0)
            one_month_price_change = _as_float(row.get("oneMonthPriceChange") or 0.0)
            one_year_price_change = _as_float(row.get("oneYearPriceChange") or 0.0)
            snapshots.append(
                MarketSnapshot(
                    market_id=market_id,
                    question=question,
                    event_title=event_title,
                    category=category,
                    probability=max(0.0, min(1.0, probability)),
                    liquidity=max(0.0, liquidity),
                    volume_24h=max(0.0, volume_24h),
                    yes_token_id=yes_token_id,
                    yes_price=max(0.001, min(0.999, yes_price)),
                    expiration_iso=expiration_iso,
                    cashout_iso=cashout_iso,
                    one_hour_price_change=one_hour_price_change,
                    one_week_price_change=one_week_price_change,
                    one_month_price_change=one_month_price_change,
                    one_year_price_change=one_year_price_change,
                )
            )
        return snapshots

    def _fetch_all_market_rows(self) -> list[dict]:
        page_size = 500
        offset = 0
        merged: list[dict] = []
        seen_ids: set[str] = set()
        for _ in range(30):
            endpoint = (
                "https://gamma-api.polymarket.com/markets"
                f"?active=true&closed=false&limit={page_size}&offset={offset}"
            )
            payload = self._fetch_payload(endpoint)
            rows = payload if isinstance(payload, list) else payload.get("data", [])
            if not isinstance(rows, list) or not rows:
                break
            added_this_page = 0
            for row in rows:
                if not isinstance(row, dict):
                    continue
                market_id = str(
                    row.get("id")
                    or row.get("market_slug")
                    or row.get("slug")
                    or row.get("questionID")
                    or ""
                )
                if not market_id or market_id in seen_ids:
                    continue
                seen_ids.add(market_id)
                merged.append(row)
                added_this_page += 1
            if added_this_page == 0:
                # Defensive break if backend ignores offset and keeps returning
                # the same page; avoids slow repeated requests.
                break
            if len(rows) < page_size:
                break
            offset += page_size
        return merged

    def _fetch_payload(self, endpoint: str) -> object:
        # Public gamma markets are typically accessible without auth and may
        # reject bot-like default clients. Use browser-style headers first.
        req = request.Request(endpoint, headers=self._headers(include_auth=False))
        try:
            with request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            # If the endpoint expects auth, retry with bearer credentials.
            if exc.code in (401, 403) and self.api_key:
                fallback_req = request.Request(
                    endpoint, headers=self._headers(include_auth=True)
                )
                with request.urlopen(fallback_req, timeout=10) as response:
                    return json.loads(response.read().decode("utf-8"))
            raise

    def _headers(self, include_auth: bool) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://polymarket.com",
            "Referer": "https://polymarket.com/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        }
        if include_auth and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_json_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return []
    return []


def _extract_event_title(row: dict) -> str:
    events = row.get("events")
    if isinstance(events, list) and events:
        first = events[0]
        if isinstance(first, dict):
            title = first.get("title")
            if title:
                return str(title)
    return str(row.get("event_title") or row.get("category") or "")


def _classify_market_category(*, question: str, event_title: str) -> str:
    text = f"{question} {event_title}".lower()
    keyword_to_category = [
        (("trump", "primary", "midterm", "senate", "election"), "global elections"),
        (("iran", "israel", "ukraine", "china", "tariff"), "geopolitics"),
        (("fed", "rate", "fomc"), "fed"),
        (("btc", "bitcoin", "eth", "crypto"), "crypto prices"),
        (("gold", "silver", "oil", "commodity"), "commodities"),
        (("oscars", "movie", "film"), "movies"),
        (("weather", "hurricane", "snow"), "weather"),
        (("ai", "model", "openai", "anthropic"), "ai"),
        (("earnings", "ipo", "stock"), "equities"),
        (("spacex", "rocket", "space"), "spacex"),
    ]
    for keywords, category in keyword_to_category:
        if any(keyword in text for keyword in keywords):
            return category
    return "all"

