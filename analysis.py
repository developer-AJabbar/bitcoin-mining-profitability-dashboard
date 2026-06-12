"""
analysis.py
Phase 2 — Bitcoin Mining Profitability Analytics Pipeline

Run AFTER collect_data.py:
    python analysis.py

Inputs:  data/master_mining_data.csv
Outputs:
    data/analysis/monthly_summary.csv
    data/analysis/profitability_bands.csv
    data/analysis/cost_breakdown.csv
    data/analysis/difficulty_impact.csv
    data/analysis/halving_comparison.csv
    data/analysis/kpi_summary.json
    reports/mining_analysis_report.txt
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

os.makedirs('data/analysis', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════

def load_data():
    path = 'data/master_mining_data.csv'
    if not os.path.exists(path):
        raise FileNotFoundError(
            "master_mining_data.csv not found.\n"
            "Run collect_data.py first."
        )
    df = pd.read_csv(path, parse_dates=['date'])
    df = df.sort_values('date').reset_index(drop=True)
    print(f"Loaded {len(df):,} rows | {df['date'].min().date()} → {df['date'].max().date()}")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 1. TOP-LINE KPIs
# ═══════════════════════════════════════════════════════════════════════════════

def compute_kpis(df):
    total_days       = len(df)
    profitable_days  = df['is_profitable'].sum()
    total_revenue    = df['daily_revenue_usd'].sum()
    total_cost       = df['total_cost_usd'].sum()
    gross_profit     = df['gross_profit_usd'].sum()
    total_btc_mined  = df['btc_mined_daily'].sum()
    avg_margin       = gross_profit / total_revenue * 100 if total_revenue else 0
    avg_btc_price    = df['btc_price_usd'].mean()
    avg_breakeven    = df['breakeven_btc_price'].mean()
    best_day         = df.loc[df['gross_profit_usd'].idxmax()]
    worst_day        = df.loc[df['gross_profit_usd'].idxmin()]
    avg_roi          = df['roi_annualized_pct'].mean()
    avg_rev_per_kwh  = df['revenue_per_kwh'].mean()

    # Peak and trough BTC price
    max_price_row = df.loc[df['btc_price_usd'].idxmax()]
    min_price_row = df.loc[df['btc_price_usd'].idxmin()]

    kpis = {
        'period':               f"{df['date'].min().date()} to {df['date'].max().date()}",
        'total_days':           total_days,
        'profitable_days':      int(profitable_days),
        'unprofitable_days':    int(total_days - profitable_days),
        'profitability_rate':   round(profitable_days / total_days * 100, 1),
        'total_revenue_usd':    round(total_revenue, 2),
        'total_cost_usd':       round(total_cost, 2),
        'gross_profit_usd':     round(gross_profit, 2),
        'total_btc_mined':      round(total_btc_mined, 6),
        'avg_profit_margin_pct':round(avg_margin, 2),
        'avg_btc_price_usd':    round(avg_btc_price, 2),
        'avg_breakeven_price':  round(avg_breakeven, 2),
        'breakeven_gap_pct':    round((avg_btc_price - avg_breakeven) / avg_breakeven * 100, 1),
        'avg_annualized_roi':   round(avg_roi, 1),
        'avg_revenue_per_kwh':  round(avg_rev_per_kwh, 4),
        'best_day':             str(best_day['date'].date()),
        'best_day_profit':      round(float(best_day['gross_profit_usd']), 2),
        'worst_day':            str(worst_day['date'].date()),
        'worst_day_profit':     round(float(worst_day['gross_profit_usd']), 2),
        'peak_btc_price':       round(float(max_price_row['btc_price_usd']), 2),
        'peak_price_date':      str(max_price_row['date'].date()),
        'lowest_btc_price':     round(float(min_price_row['btc_price_usd']), 2),
        'lowest_price_date':    str(min_price_row['date'].date()),
    }

    with open('data/analysis/kpi_summary.json', 'w', encoding='utf-8') as f:
        json.dump(kpis, f, indent=2)

    return kpis


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MONTHLY SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def monthly_summary(df):
    """Aggregate all metrics by month — primary Power BI time-series source."""

    monthly = df.groupby(['year', 'month', 'month_name']).agg(
        days            = ('date', 'count'),
        profitable_days = ('is_profitable', 'sum'),
        total_revenue   = ('daily_revenue_usd', 'sum'),
        total_cost      = ('total_cost_usd', 'sum'),
        elec_cost       = ('daily_elec_cost_usd', 'sum'),
        pool_fees       = ('pool_fee_usd', 'sum'),
        other_opex      = ('opex_other_usd', 'sum'),
        gross_profit    = ('gross_profit_usd', 'sum'),
        btc_mined       = ('btc_mined_daily', 'sum'),
        avg_btc_price   = ('btc_price_usd', 'mean'),
        max_btc_price   = ('btc_price_usd', 'max'),
        min_btc_price   = ('btc_price_usd', 'min'),
        avg_breakeven   = ('breakeven_btc_price', 'mean'),
        avg_hashrate    = ('fleet_hashrate_ths', 'mean'),
        avg_difficulty  = ('network_hashrate_ths', 'mean'),
        avg_roi         = ('roi_annualized_pct', 'mean'),
        total_kwh       = ('daily_power_kwh', 'sum'),
        avg_rev_kwh     = ('revenue_per_kwh', 'mean'),
    ).reset_index()

    # Derived columns
    monthly['profit_margin_pct']     = (monthly['gross_profit'] / monthly['total_revenue'] * 100).round(2)
    monthly['profitability_rate_pct']= (monthly['profitable_days'] / monthly['days'] * 100).round(1)
    monthly['elec_pct_of_cost']      = (monthly['elec_cost'] / monthly['total_cost'] * 100).round(1)
    monthly['cost_per_btc']          = (monthly['total_cost'] / monthly['btc_mined']).round(2)
    monthly['revenue_per_btc']       = (monthly['total_revenue'] / monthly['btc_mined']).round(2)
    monthly['breakeven_gap_pct']     = ((monthly['avg_btc_price'] - monthly['avg_breakeven']) / monthly['avg_breakeven'] * 100).round(1)

    # MoM changes
    monthly['revenue_mom_pct']  = monthly['total_revenue'].pct_change().mul(100).round(1)
    monthly['profit_mom_pct']   = monthly['gross_profit'].pct_change().mul(100).round(1)
    monthly['price_mom_pct']    = monthly['avg_btc_price'].pct_change().mul(100).round(1)

    # Cumulative profit
    monthly['cumulative_profit'] = monthly['gross_profit'].cumsum().round(2)
    monthly['cumulative_revenue']= monthly['total_revenue'].cumsum().round(2)

    # Round numeric cols
    for col in ['total_revenue','total_cost','elec_cost','pool_fees','gross_profit',
                'avg_btc_price','max_btc_price','min_btc_price','avg_breakeven']:
        monthly[col] = monthly[col].round(2)
    monthly['btc_mined']    = monthly['btc_mined'].round(6)
    monthly['total_kwh']    = monthly['total_kwh'].round(0)
    monthly['avg_roi']      = monthly['avg_roi'].round(1)

    monthly.to_csv('data/analysis/monthly_summary.csv', index=False)
    print(f"  monthly_summary.csv         → {len(monthly)} months")
    return monthly


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PROFITABILITY BANDS — how often each price range is profitable
# ═══════════════════════════════════════════════════════════════════════════════

def profitability_bands(df):
    """
    Bin BTC price into $5K bands and compute profitability metrics per band.
    Useful for the break-even chart in Power BI.
    """
    df = df.copy()
    df['price_band'] = (df['btc_price_usd'] // 5000 * 5000).astype(int)
    df['price_band_label'] = df['price_band'].apply(lambda x: f"${x:,}–${x+5000:,}")

    bands = df.groupby(['price_band', 'price_band_label']).agg(
        days             = ('date', 'count'),
        profitable_days  = ('is_profitable', 'sum'),
        avg_profit       = ('gross_profit_usd', 'mean'),
        avg_margin       = ('profit_margin_pct', 'mean'),
        avg_breakeven    = ('breakeven_btc_price', 'mean'),
        avg_roi          = ('roi_annualized_pct', 'mean'),
    ).reset_index().sort_values('price_band')

    bands['profitability_rate_pct'] = (bands['profitable_days'] / bands['days'] * 100).round(1)
    bands['avg_profit']             = bands['avg_profit'].round(2)
    bands['avg_margin']             = bands['avg_margin'].round(2)
    bands['avg_breakeven']          = bands['avg_breakeven'].round(2)
    bands['avg_roi']                = bands['avg_roi'].round(1)

    bands.to_csv('data/analysis/profitability_bands.csv', index=False)
    print(f"  profitability_bands.csv     → {len(bands)} price bands")
    return bands


# ═══════════════════════════════════════════════════════════════════════════════
# 4. COST BREAKDOWN — granular cost analysis per period
# ═══════════════════════════════════════════════════════════════════════════════

def cost_breakdown(df):
    """
    Melt cost components into a long-form table for Power BI stacked charts.
    """
    monthly = df.groupby('month_name').agg(
        electricity = ('daily_elec_cost_usd', 'sum'),
        pool_fees   = ('pool_fee_usd', 'sum'),
        other_opex  = ('opex_other_usd', 'sum'),
        total_cost  = ('total_cost_usd', 'sum'),
        revenue     = ('daily_revenue_usd', 'sum'),
        year        = ('year', 'first'),
        month       = ('month', 'first'),
    ).reset_index().sort_values(['year', 'month'])

    # Wide format for donut/waterfall
    for col in ['electricity','pool_fees','other_opex','total_cost','revenue']:
        monthly[col] = monthly[col].round(2)

    monthly['elec_pct']   = (monthly['electricity'] / monthly['total_cost'] * 100).round(1)
    monthly['pool_pct']   = (monthly['pool_fees']   / monthly['total_cost'] * 100).round(1)
    monthly['other_pct']  = (monthly['other_opex']  / monthly['total_cost'] * 100).round(1)

    monthly.to_csv('data/analysis/cost_breakdown.csv', index=False)
    print(f"  cost_breakdown.csv          → {len(monthly)} months")

    # Also save long-form for stacked bar charts
    long = monthly.melt(
        id_vars=['month_name','year','month'],
        value_vars=['electricity','pool_fees','other_opex'],
        var_name='cost_type',
        value_name='amount_usd'
    )
    long.to_csv('data/analysis/cost_breakdown_long.csv', index=False)
    return monthly


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DIFFICULTY IMPACT — how network difficulty compresses earnings
# ═══════════════════════════════════════════════════════════════════════════════

def difficulty_impact(df):
    """
    Analyse how rising network difficulty erodes per-unit mining income.
    """
    d = df.copy()

    # Normalize difficulty and hashrate to index (base = first period)
    base_diff  = d['difficulty'].iloc[0]
    base_hash  = d['network_hashrate_ths'].iloc[0]
    base_rev   = d['daily_revenue_usd'].iloc[0]

    d['difficulty_index']  = (d['difficulty']           / base_diff * 100).round(2)
    d['hashrate_index']    = (d['network_hashrate_ths'] / base_hash * 100).round(2)
    d['revenue_index']     = (d['daily_revenue_usd']    / base_rev  * 100).round(2)

    # Revenue compression = revenue change attributable to difficulty
    d['revenue_vs_price']  = (d['btc_price_usd'] / d['btc_price_usd'].iloc[0] * 100).round(2)
    d['difficulty_drag']   = (d['revenue_index'] - d['revenue_vs_price']).round(2)

    # Earnings efficiency: BTC mined per TH/s per day
    d['btc_per_ths'] = (d['btc_mined_daily'] / d['fleet_hashrate_ths']).round(10)

    result = d[['date','btc_price_usd','difficulty','network_hashrate_ths',
                'difficulty_index','hashrate_index','revenue_index',
                'revenue_vs_price','difficulty_drag','btc_per_ths',
                'btc_mined_daily','daily_revenue_usd']]

    result.to_csv('data/analysis/difficulty_impact.csv', index=False)
    print(f"  difficulty_impact.csv       → {len(result)} rows")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 6. HALVING COMPARISON — before vs after the April 2024 halving
# ═══════════════════════════════════════════════════════════════════════════════

def halving_comparison(df):
    """
    Compare key metrics before and after the April 2024 halving event.
    """
    HALVING_DATE = pd.Timestamp('2024-04-20')

    pre  = df[df['date'] < HALVING_DATE].copy()
    post = df[df['date'] >= HALVING_DATE].copy()

    def summarise(segment, label):
        if len(segment) == 0:
            return {}
        return {
            'period':               label,
            'days':                 len(segment),
            'avg_daily_revenue':    round(segment['daily_revenue_usd'].mean(), 2),
            'avg_daily_cost':       round(segment['total_cost_usd'].mean(), 2),
            'avg_daily_profit':     round(segment['gross_profit_usd'].mean(), 2),
            'avg_margin_pct':       round(segment['profit_margin_pct'].mean(), 2),
            'avg_btc_price':        round(segment['btc_price_usd'].mean(), 2),
            'avg_btc_mined':        round(segment['btc_mined_daily'].mean(), 6),
            'avg_breakeven_price':  round(segment['breakeven_btc_price'].mean(), 2),
            'profitability_rate':   round(segment['is_profitable'].mean() * 100, 1),
            'block_reward':         round(segment['block_reward_btc'].mean(), 4),
        }

    rows = [summarise(pre, 'Pre-Halving (6.25 BTC)'),
            summarise(post, 'Post-Halving (3.125 BTC)')]
    rows = [r for r in rows if r]

    comp = pd.DataFrame(rows)
    comp.to_csv('data/analysis/halving_comparison.csv', index=False)
    print(f"  halving_comparison.csv      → {len(comp)} periods")
    return comp


# ═══════════════════════════════════════════════════════════════════════════════
# 7. BREAK-EVEN SENSITIVITY TABLE
# ═══════════════════════════════════════════════════════════════════════════════

def breakeven_sensitivity(df):
    """
    What-if table: profit at different BTC prices × electricity costs.
    Shows how sensitive margins are to each variable.
    """
    btc_prices = range(20000, 105000, 5000)
    elec_costs  = [0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]

    avg_btc_mined  = df['btc_mined_daily'].mean()
    avg_power_kwh  = df['daily_power_kwh'].mean()

    rows = []
    for price in btc_prices:
        for elec in elec_costs:
            revenue  = price * avg_btc_mined
            elec_usd = avg_power_kwh * elec
            pool_fee = revenue * 0.02
            other    = revenue * 0.05
            cost     = elec_usd + pool_fee + other
            profit   = revenue - cost
            margin   = profit / revenue * 100 if revenue else 0
            breakeven_price = cost / avg_btc_mined if avg_btc_mined else 0
            rows.append({
                'btc_price':          price,
                'electricity_cost_kwh': elec,
                'daily_revenue':      round(revenue, 2),
                'daily_cost':         round(cost, 2),
                'daily_profit':       round(profit, 2),
                'margin_pct':         round(margin, 1),
                'breakeven_price':    round(breakeven_price, 2),
                'is_profitable':      int(profit > 0),
            })

    sensitivity = pd.DataFrame(rows)
    sensitivity.to_csv('data/analysis/breakeven_sensitivity.csv', index=False)
    print(f"  breakeven_sensitivity.csv   → {len(sensitivity)} scenarios")
    return sensitivity


# ═══════════════════════════════════════════════════════════════════════════════
# 8. TEXT REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(kpis, monthly, bands, halving):
    lines = []
    lines.append("=" * 60)
    lines.append("  BITCOIN MINING PROFITABILITY — ANALYSIS REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)

    lines.append("\n── TOP-LINE KPIs ──────────────────────────────────────────")
    lines.append(f"  Period               : {kpis['period']}")
    lines.append(f"  Total Revenue        : ${kpis['total_revenue_usd']:>12,.2f}")
    lines.append(f"  Total Cost           : ${kpis['total_cost_usd']:>12,.2f}")
    lines.append(f"  Gross Profit         : ${kpis['gross_profit_usd']:>12,.2f}")
    lines.append(f"  Avg Profit Margin    : {kpis['avg_profit_margin_pct']:>10.1f}%")
    lines.append(f"  Total BTC Mined      : {kpis['total_btc_mined']:>12.4f} BTC")
    lines.append(f"  Profitable Days      : {kpis['profitable_days']:>5} / {kpis['total_days']} ({kpis['profitability_rate']}%)")

    lines.append("\n── PRICE & BREAK-EVEN ─────────────────────────────────────")
    lines.append(f"  Avg BTC Price        : ${kpis['avg_btc_price_usd']:>12,.2f}")
    lines.append(f"  Avg Break-even Price : ${kpis['avg_breakeven_price']:>12,.2f}")
    lines.append(f"  Break-even Gap       : {kpis['breakeven_gap_pct']:>10.1f}% above break-even")
    lines.append(f"  Peak BTC Price       : ${kpis['peak_btc_price']:>12,.2f}  ({kpis['peak_price_date']})")
    lines.append(f"  Lowest BTC Price     : ${kpis['lowest_btc_price']:>12,.2f}  ({kpis['lowest_price_date']})")

    lines.append("\n── BEST & WORST DAYS ──────────────────────────────────────")
    lines.append(f"  Best Day  : {kpis['best_day']}   Profit = ${kpis['best_day_profit']:>10,.2f}")
    lines.append(f"  Worst Day : {kpis['worst_day']}   Profit = ${kpis['worst_day_profit']:>10,.2f}")

    if len(halving) >= 2:
        lines.append("\n── HALVING IMPACT ─────────────────────────────────────────")
        pre  = halving.iloc[0]
        post = halving.iloc[1]
        lines.append(f"  Pre-halving avg daily revenue  : ${pre['avg_daily_revenue']:>10,.2f}")
        lines.append(f"  Post-halving avg daily revenue : ${post['avg_daily_revenue']:>10,.2f}")
        rev_change = (post['avg_daily_revenue'] - pre['avg_daily_revenue']) / pre['avg_daily_revenue'] * 100
        lines.append(f"  Revenue change after halving   : {rev_change:>10.1f}%")

    lines.append("\n── BEST PRICE BAND FOR PROFITABILITY ──────────────────────")
    top_bands = bands.nlargest(3, 'avg_profit')[['price_band_label','avg_profit','avg_margin','profitability_rate_pct']]
    for _, row in top_bands.iterrows():
        lines.append(f"  {row['price_band_label']:<16}  Avg Profit/day=${row['avg_profit']:>8,.0f}  "
                     f"Margin={row['avg_margin']:>5.1f}%  Profitable={row['profitability_rate_pct']}% of days")

    lines.append("\n" + "=" * 60)
    lines.append("  Output files in data/analysis/")
    lines.append("  → Import monthly_summary.csv into Power BI")
    lines.append("  → Use breakeven_sensitivity.csv for What-If page")
    lines.append("=" * 60)

    report = "\n".join(lines)
    with open('reports/mining_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print("\n" + report)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 55)
    print("  Bitcoin Mining BI — Phase 2: Analytics Pipeline")
    print("=" * 55 + "\n")

    df = load_data()
    print()

    print("Running analyses...\n")
    kpis    = compute_kpis(df)
    monthly = monthly_summary(df)
    bands   = profitability_bands(df)
    costs   = cost_breakdown(df)
    diff    = difficulty_impact(df)
    halving = halving_comparison(df)
    sens    = breakeven_sensitivity(df)

    generate_report(kpis, monthly, bands, halving)

    print("\n✅ All analysis files saved to data/analysis/")
    print("\n── Power BI Import Order ───────────────────────────────")
    print("  1. data/master_mining_data.csv       (daily fact table)")
    print("  2. data/analysis/monthly_summary.csv (monthly aggregates)")
    print("  3. data/analysis/cost_breakdown.csv  (cost structure)")
    print("  4. data/analysis/breakeven_sensitivity.csv (what-if table)")
    print("  5. data/miner_fleet.csv              (hardware dimension)")
