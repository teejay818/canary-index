#!/usr/bin/env python3
import json, pandas as pd, numpy as np
from datetime import datetime, timedelta
import yfinance as yf

CANARY = [
  "OLLI","HBI","MAS","BLDR","BLD","OC","FIVE","KBH","URBN","TGT",
  "BBY","DDS","LEN","WSM","MTH","FND","ANF","EBAY","LOW","DHI",
  "BBW","AEO","PHM","DKS","M","BBWI"
]

def ew_series(df):
    daily = df.pct_change().mean(axis=1)
    return (1.0 + daily).cumprod() - 1.0

def mc_series(df, caps):
    w = (caps / caps.sum()).reindex(df.columns).fillna(0.0)
    daily = (df.pct_change() * w).sum(axis=1)
    return (1.0 + daily).cumprod() - 1.0

def period_ret(series, start_dt):
    sub = series[series.index >= start_dt]
    if len(sub) < 2:
        return None
    return float(sub.iloc[-1] - sub.iloc[0])

def component_returns(df, start_dt):
    sub = df[df.index >= start_dt]
    if len(sub) < 2:
        return pd.Series(dtype="float64")
    return sub.iloc[-1] / sub.iloc[0] - 1.0

def contributors_mc(ret_series, caps):
    w = (caps / caps.sum()).reindex(ret_series.index).fillna(0.0)
    return ret_series * w

def main():
    end = datetime.utcnow()
    start = end - timedelta(days=550)
    px = yf.download(CANARY, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), auto_adjust=True, progress=False)["Close"].dropna(axis=1, how="all")
    aligned = [t for t in CANARY if t in px.columns]
    px = px[aligned]

    info = yf.Tickers(" ".join(aligned))
    caps = {}
    for t in aligned:
        cap = None
        try:
            fi = getattr(info.tickers.get(t), "fast_info", None)
            if fi and getattr(fi, "market_cap", None):
                cap = fi.market_cap
        except Exception:
            pass
        if not cap:
            try:
                cap = getattr(info.tickers.get(t), "info", {}).get("marketCap")
            except Exception:
                cap = None
        caps[t] = cap if cap else 0.0
    caps = pd.Series(caps, dtype="float64")

    ew = ew_series(px)
    mc = mc_series(px, caps)

    today = px.index.max()
    PERIODS = {
        "1D": px.index[-2],
        "3M": today - pd.DateOffset(months=3),
        "YTD": pd.Timestamp(today.year, 1, 1),
        "12M": today - pd.DateOffset(years=1),
    }

    def basket_block(series):
        return {
            "1D":  (float(series.iloc[-1] - series.iloc[-2]) if len(series) >= 2 else None),
            "3M":  period_ret(series, PERIODS["3M"]),
            "YTD": period_ret(series, PERIODS["YTD"]),
            "12M": period_ret(series, PERIODS["12M"]),
        }

    leaders = {}
    for label, start_dt in PERIODS.items():
        r = component_returns(px, start_dt)
        if r.empty:
            leaders[label] = None
            continue
        best = {"ticker": r.idxmax(), "return": float(r.max())}
        worst = {"ticker": r.idxmin(), "return": float(r.min())}
        contrib = contributors_mc(r, caps)
        topc = {"ticker": contrib.idxmax(), "contribution": float(contrib.max())}
        botc = {"ticker": contrib.idxmin(), "contribution": float(contrib.min())}
        leaders[label] = {
            "best": best,
            "worst": worst,
            "top_contributor_mc": topc,
            "bottom_contributor_mc": botc
        }

    out = {
      "as_of_utc": today.strftime("%Y-%m-%dT%H:%M:%SZ"),
      "canary_members": aligned,
      "CanaryEW": basket_block(ew),
      "CanaryMC": basket_block(mc),
      "leaders_laggards": leaders
    }

    with open("docs/canary.json","w") as f:
        json.dump(out, f, indent=2)
    print("Wrote docs/canary.json (members: %d)" % len(aligned))

if __name__ == "__main__":
    main()