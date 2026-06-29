---
title: Dataset — CoinMarketCap daily panel
type: entity
source: "arXiv:2604.26747v1"
tags: [entity, dataset, coinmarketcap, data]
status: verified
last_reviewed: 2026-06-24
---

# Dataset — CoinMarketCap daily panel

- **Provider:** CoinMarketCap (CMC).
- **Frequency:** daily.
- **Span:** Jan 2020 – Dec 2025.
- **Fields used:** OHLC, volume, **market cap**, returns, log returns, relative volume,
  realized vol, price-to-MA, high-low range, volume %Δ (see [[constrained-factor-dsl]]).
- **Universe filter:** drop < 180 days history or below-threshold avg daily volume.
- **Splits:** train 2020–2022 / valid 2023 / OOS 2024–2026.

## Caveats (mine)
- CMC market cap and volume are **aggregated across venues** and historically subject to
  wash-trading / inflated-volume issues → the "volume" and "relative volume" features may
  be noisier than exchange-native data. Relevant because failed-signal analysis blamed
  "volume recovery" noise — partly a *data-quality* artifact, not only a market fact.
- Not point-in-time confirmed → see [[survivorship-and-universe]].
- **Mismatch with my venue:** I trade Binance USDⓈ-M perps. CMC spot market-cap/volume ≠
  Binance perp mark price / contract volume / open interest. Porting requires a venue swap,
  not just a reformat. See [[_adaptation]].

Related: [[2604-26747]] · [[survivorship-and-universe]] · [[capacity-constraint]]
