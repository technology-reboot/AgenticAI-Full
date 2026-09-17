from dataclasses import dataclass


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    price: float | None
    source: str
    status: str


def fetch_prices(symbols: list[str]) -> tuple[MarketSnapshot, ...]:
    """Fetch prices when yfinance is installed; return a clear unavailable state otherwise."""
    try:
        import yfinance as yf
    except ImportError:
        return tuple(MarketSnapshot(symbol, None, "yfinance", "unavailable") for symbol in symbols)
    snapshots = []
    for symbol in symbols:
        try:
            history = yf.Ticker(symbol).history(period="1d")
            price = float(history["Close"].iloc[-1]) if not history.empty else None
            snapshots.append(MarketSnapshot(symbol, price, "yfinance", "ok" if price else "empty"))
        except Exception:
            snapshots.append(MarketSnapshot(symbol, None, "yfinance", "error"))
    return tuple(snapshots)