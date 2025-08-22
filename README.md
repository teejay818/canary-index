# Canary Index JSON Publisher

Publishes **CanaryEW** (equal-weight) and **CanaryMC** (market-cap-weight) performance plus leaders/laggards to `docs/canary.json` for hosting on GitHub Pages.

## Files
- `compute.py` — pulls prices via yfinance, computes returns, writes `docs/canary.json`
- `requirements.txt` — Python deps
- `.github/workflows/canary.yml` — GitHub Action (runs daily after US market close)
- `docs/canary.json` — placeholder output file

## How to use
1. Create a repo with these files.
2. Enable Pages: **Settings → Pages →** Branch: `main`, Folder: `/docs`.
3. (Optional) Set a custom domain like `canary.120proofball.com` in Pages.
4. Add a GoDaddy CNAME for the subdomain pointing to `<your-username>.github.io`.

Now fetch `https://canary.120proofball.com/canary.json` whenever you want the latest snapshot.
