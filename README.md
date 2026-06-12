# ₿ Bitcoin Mining Profitability Intelligence Dashboard

> **Portfolio Project 1** — Data Analyst & BI Specialist | Crypto & Energy Analytics
> **Author:** Danish Akhtar
> **Tools:** Python · Power BI · DAX · CoinGecko API · Blockchain.com API

---

## 📌 Project Overview

This end-to-end Business Intelligence project analyzes the profitability of a
135-unit Bitcoin mining fleet across a 2-year period (January 2022 – December 2023).
It combines real market data from public APIs with a realistic miner hardware model
to answer the most critical questions in mining operations:

- Is the operation profitable today — and why?
- At what BTC price does the fleet break even?
- How does network difficulty compress earnings over time?
- What happens to profit if electricity costs rise or BTC price changes?

---

## 📊 Dashboard — 5 Pages

### Page 1 — Executive Summary
**Visuals:** 5 KPI cards · Line chart · Gauge chart · Bar chart · Year slicer

| KPI | Value |
|-----|-------|
| Total BTC Mined | 5.60 BTC |
| Total Revenue | $163,017 |
| Gross Profit | $102,429 |
| Overall Margin % | 62.83% |
| Profitable Days | 91 / 91 (100%) |

Key insight: The gauge shows BTC price ($28,250) sitting well above the
break-even price ($10,870) — a 103% safety cushion. The bar chart reveals
2022 months generated significantly higher monthly profit than 2023 due to
higher BTC prices in early 2022.

---

### Page 2 — Profitability Analysis
**Visuals:** Area chart · Combo chart · Scatter plot · Matrix table · 2 KPI cards · Quarter slicer

| Metric | Value |
|--------|-------|
| Cumulative Profit | $139,919 |
| Avg Break-even Price | $14,040 |
| Break-even Gap % | 103.05% |
| Annualized ROI % | 41,653% |

Monthly performance from dashboard:

| Month | Revenue | Cost | Profit | Margin |
|-------|---------|------|--------|--------|
| April 2022 | $29,340 | $10,160 | $19,180 | 59.43% |
| March 2022 | $27,830 | $10,054 | $17,776 | 56.03% |
| February 2022 | $27,410 | $9,484 | $17,926 | 58.56% |
| August 2023 | $19,172 | $9,988 | $9,184 | 45.81% |
| December 2023 | $15,125 | $9,165 | $5,960 | 38.45% |
| **Total** | **$256,206** | **$116,287** | **$139,919** | **48.00%** |

Key insight: Scatter plot proves strong positive correlation between BTC
price and gross profit. April 2022 was the most profitable month at 59.43%
margin. Late 2023 compressed to 36-38% margins.

---

### Page 3 — Cost Analysis
**Visuals:** Donut chart · Stacked column chart · Line chart · 4 KPI cards

| Cost Metric | Value |
|-------------|-------|
| Electricity (84.58%) | $98,350 |
| Other OPEX (11.02%) | $12,810 |
| Pool Fees (4.40%) | $5,124 |
| Avg Daily Electricity Cost | $540.40 |
| Avg Daily Power Usage | 10,560 kWh |
| Avg Electricity Rate | $0.05/kWh |
| Revenue per kWh | $0.13 |

Key insight: Electricity dominates at 84.58% of total cost. Revenue per
kWh declined sharply from $0.30 in early 2022 to $0.10 during bear market
— directly tracking BTC price movements.

---

### Page 4 — Forecasting
**Visuals:** Line chart with forecast · Cumulative profit chart · YoY bar chart · 4 KPI cards

| Metric | Value |
|--------|-------|
| Revenue 30D Moving Average | $1,130/day |
| Forecast | Extends to mid-2024 |

Key insight: The forecast line extends through 2024 showing projected
recovery. YoY comparison shows 2022 significantly outperforming 2023 in
the first half but 2023 showing more stability in H2.

---

### Page 5 — What-If Analysis
**Visuals:** BTC Price slider · Electricity Cost slider · 4 live KPI cards · Profit curve line chart

Live scenario at BTC $25,000 / Electricity $0.04/kWh:

| Metric | Value |
|--------|-------|
| Scenario Daily Revenue | $1,228.66 |
| Scenario Daily Profit | $614.40 |
| Scenario Margin % | 50.01% |
| Scenario Break-even Price | $11,500.88 |

Key insight: The profit curve shows the full range from BTC $10,000 to
$100,000. At $100,000 BTC daily profit reaches $4,000+. Moving the
electricity slider instantly shows profit compression — proving why
cheap electricity is the most critical factor in mining profitability.

---

## 🗂️ Project Structure

```
bitcoin-mining-profitability-dashboard/
│
├── collect_data.py                   Data collection from APIs
├── analysis.py                       Analytics pipeline
├── dax_measures.txt                  All 34 DAX measures
├── Bitcoin_Mining_Summary.txt        Written executive summary
├── Bitcoin_Mining_Dashboard.pdf      Power BI dashboard export
├── README.md                         This file
│
├── data/
│   ├── btc_price_history.csv         BTC daily price (CoinGecko API)
│   ├── btc_network_data.csv          Network hashrate and difficulty
│   ├── miner_fleet.csv               135-unit miner hardware dataset
│   ├── master_mining_data.csv        Merged daily fact table (182 rows)
│   │
│   └── analysis/
│       ├── monthly_summary.csv       24-month aggregated metrics
│       ├── cost_breakdown.csv        Monthly cost components
│       ├── breakeven_sensitivity.csv 136 what-if scenarios
│       ├── difficulty_impact.csv     Network difficulty analysis
│       └── halving_comparison.csv    Pre vs post halving data
│
└── screenshots/
    ├── page1.png
    ├── page2.png
    ├── page3.png
    ├── page4.png
    └── page5.png
```

---

## 🚀 How to Run

### Step 1 — Install dependencies
```bash
pip install requests pandas numpy
```

### Step 2 — Collect real data
```bash
python collect_data.py
```

### Step 3 — Run analytics pipeline
```bash
python analysis.py
```

### Step 4 — Open Power BI
1. Home → Get Data → Text/CSV
2. Import master_mining_data.csv → rename to MiningData
3. Import monthly_summary.csv → rename to MonthlySummary
4. Import cost_breakdown.csv → rename to CostBreakdown
5. Import breakeven_sensitivity.csv → rename to BreakevenScenarios
6. Import miner_fleet.csv → rename to MinerFleet
7. Fix date column: Transform Data → date → Change Type → Date
8. Add all DAX measures from dax_measures.txt

---

## 📐 DAX Measures — 34 Total

| Page | Measures |
|------|----------|
| Page 1 Executive Summary | Total Revenue · Total Cost · Gross Profit · Overall Margin % · Total BTC Mined · Profitable Days · Avg BTC Price · Avg Breakeven Price |
| Page 2 Profitability | Break-even Gap % · Annualized ROI % · Profit Margin % · Cumulative Profit · Revenue MoM % |
| Page 3 Cost Analysis | Total Electricity Cost · Total Pool Fees · Total Other OPEX · Electricity % of Cost · Cost per BTC · Avg Daily kWh · Avg Electricity Rate · Revenue per kWh |
| Page 4 Forecasting | Revenue 30D MA · Profit 30D MA · Revenue YoY % |
| Page 5 What-If | Scenario Daily Revenue · Scenario Elec Cost · Scenario Daily Profit · Scenario Margin % · Scenario Breakeven Price · Scenario Annual Profit · Profit At Price · Scenario Profit · Scenario Revenue · Scenario Annual |

---

## 🔑 Key Findings

```
Total Revenue        $256,206   2-year cumulative
Gross Profit         $139,919   after all costs
Profit Margin        54.6%      blended margin
Total BTC Mined      8.94 BTC
Profitable Days      182/182    100% profitability rate
Avg BTC Price        $28,509
Break-even Price     $14,040
Break-even Cushion   103.1%     above break-even
Best Day Profit      $2,742     January 3 2022
Worst Day Profit     $222       November 27 2022 FTX crash
```

---

## 🏭 Miner Fleet

| Model | Units | Hashrate | Power |
|-------|-------|----------|-------|
| Antminer S19 | 50 | 95 TH/s | 3,250W |
| Antminer S19 Pro | 30 | 110 TH/s | 3,250W |
| Antminer S19 XP | 20 | 140 TH/s | 3,010W |
| Antminer S21 | 10 | 200 TH/s | 3,500W |
| Whatsminer M30S | 25 | 90 TH/s | 3,400W |
| **Total** | **135** | **~13,200 TH/s** | **~0.41 MW** |

---

## 💡 Business Insights

**1. Electricity is everything**
At $0.048/kWh the operation stayed profitable even when BTC hit $16,428
during the FTX collapse. A $0.01/kWh rate increase reduces daily profit
by approximately $105.

**2. Break-even is the key number**
With a break-even price of $14,040 the fleet has a 103% safety cushion
at average BTC prices. BTC must drop below $14,040 before any loss occurs.

**3. Halving impact**
The April 2024 halving reduces block rewards from 6.25 to 3.125 BTC
— effectively doubling the break-even requirement to approximately $28,000.

**4. Bull vs bear performance**
April 2022 was the peak month at 59.43% margin ($19,180 profit).
December 2023 was the weakest at 38.45% margin ($5,960 profit).
The operation remained profitable throughout both extremes.

---

## 🧰 Tools and Technologies

| Layer | Technology |
|-------|-----------|
| Data Collection | Python · requests · CoinGecko API · Blockchain.com API |
| Data Processing | Python · Pandas · NumPy |
| Business Intelligence | Power BI Desktop |
| DAX Calculations | 34 custom measures |
| Financial Modeling | Break-even · ROI · Margin · Scenario analysis |
| Version Control | Git · GitHub |

---

## 👤 About

**Abdul Jabbar Akhtar** — Data Analyst & BI Specialist | Crypto & Energy Analytics

I help businesses turn complex messy data into clear decision-ready insights
that improve profitability, efficiency, and forecasting accuracy. With 120+
successfully completed Upwork projects and deep analytical experience across
Bitcoin mining, renewable energy, and energy sector financial modeling.

---

## 📄 License

MIT License — data sourced from public APIs. No real operational data included.
