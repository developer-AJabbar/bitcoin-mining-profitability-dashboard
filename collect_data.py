"""
collect_data.py
Phase 1 — Data Collection for Bitcoin Mining Profitability BI Dashboard

Sources:
  1. CoinGecko API  → BTC daily price + market data (free, no key needed)
  2. Mining network → Network hashrate, difficulty from Blockchain.com API
  3. Miner dataset  → Synthetic miner hardware & electricity data

Run: python collect_data.py
Output files:
  data/btc_price_history.csv
  data/btc_network_data.csv
  data/miner_fleet.csv
  data/master_mining_data.csv   ← merged, ready for Power BI
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os

os.makedirs('data', exist_ok=True)

# ─── CONFIG ──────────────────────────────────────────────────────────────────
START_DATE = '2022-01-01'   # change as needed
END_DATE   = '2024-01-01'
COIN_ID    = 'bitcoin'

# ─── 1. BTC PRICE HISTORY — CoinGecko / Binance fallback ───────────────────

def fetch_btc_price_from_binance():
    """Fallback BTC daily OHLCV feed using Binance public API."""
    print("Fetching BTC price history from Binance fallback...")

    start_ms = int(datetime.strptime(START_DATE, '%Y-%m-%d').timestamp() * 1000)
    end_ms   = int(datetime.strptime(END_DATE,   '%Y-%m-%d').timestamp() * 1000)

    url = 'https://api.binance.com/api/v3/klines'
    all_rows = []
    next_start = start_ms

    while next_start < end_ms:
        params = {
            'symbol': 'BTCUSDT',
            'interval': '1d',
            'startTime': next_start,
            'endTime': end_ms,
            'limit': 1000,
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            break

        all_rows.extend(rows)
        next_start = rows[-1][6] + 1
        if next_start >= end_ms:
            break

    if not all_rows:
        raise RuntimeError('Binance returned no BTC daily data.')

    df = pd.DataFrame(
        all_rows,
        columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ],
    )
    df = df[['close_time', 'close', 'quote_volume']].copy()
    df['date'] = pd.to_datetime(df['close_time'], unit='ms').dt.date.astype(str)
    df = df.rename(columns={'close': 'btc_price_usd', 'quote_volume': 'volume_usd'})
    df['btc_price_usd'] = pd.to_numeric(df['btc_price_usd'], errors='coerce')
    df['volume_usd'] = pd.to_numeric(df['volume_usd'], errors='coerce').fillna(0)

    df = df.groupby('date', as_index=False).agg({
        'btc_price_usd': 'last',
        'volume_usd': 'sum',
    })
    df = df[(df['date'] >= START_DATE) & (df['date'] <= END_DATE)]
    df['btc_price_usd'] = df['btc_price_usd'].round(2)
    df['volume_usd'] = df['volume_usd'].round(0).astype(int)

    df.to_csv('data/btc_price_history.csv', index=False)
    print(f"  Saved btc_price_history.csv  → {len(df)} rows")
    return df


def fetch_btc_price():
    """Fetch daily BTC OHLCV data from CoinGecko, with a Binance fallback for 401/403 auth errors."""
    print("Fetching BTC price history from CoinGecko...")

    start_ts = int(datetime.strptime(START_DATE, '%Y-%m-%d').timestamp())
    end_ts   = int(datetime.strptime(END_DATE,   '%Y-%m-%d').timestamp())

    url = f"https://api.coingecko.com/api/v3/coins/{COIN_ID}/market_chart/range"
    params = {
        'vs_currency': 'usd',
        'from': start_ts,
        'to':   end_ts,
    }
    headers = {'accept': 'application/json'}

    demo_key = os.getenv('COINGECKO_DEMO_API_KEY') or os.getenv('CG_DEMO_API_KEY')
    if demo_key:
        headers['x-cg-demo-api-key'] = demo_key

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as exc:
        if resp.status_code in (401, 403):
            print('CoinGecko returned 401/403; using Binance fallback instead.')
            return fetch_btc_price_from_binance()
        raise

    prices  = data['prices']          # [[timestamp_ms, price], ...]
    volumes = data['total_volumes']   # [[timestamp_ms, volume], ...]

    df_price = pd.DataFrame(prices,  columns=['timestamp_ms', 'btc_price_usd'])
    df_vol   = pd.DataFrame(volumes, columns=['timestamp_ms', 'volume_usd'])

    df = df_price.merge(df_vol, on='timestamp_ms')
    df['date'] = pd.to_datetime(df['timestamp_ms'], unit='ms').dt.date.astype(str)
    df = df[['date', 'btc_price_usd', 'volume_usd']].drop_duplicates('date')
    df['btc_price_usd'] = df['btc_price_usd'].round(2)
    df['volume_usd']    = df['volume_usd'].round(0).astype(int)

    df.to_csv('data/btc_price_history.csv', index=False)
    print(f"  Saved btc_price_history.csv  → {len(df)} rows")
    return df


# ─── 2. NETWORK HASHRATE & DIFFICULTY — Blockchain.com API ───────────────────
def fetch_network_data():
    """
    Fetch Bitcoin network hashrate and mining difficulty from Blockchain.com.
    Free, no API key required.
    """
    print("Fetching network hashrate & difficulty...")

    # Blockchain.com Chart API
    def get_chart(metric):
        url = f"https://api.blockchain.info/charts/{metric}"
        params = {
            'timespan':  'all',
            'format':    'json',
            'sampled':   'true',
        }
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()

        values = r.json().get('values', [])
        normalized = []
        for item in values:
            if isinstance(item, dict):
                normalized.append((item.get('x'), item.get('y')))
            else:
                normalized.append(tuple(item))
        return normalized

    hashrate   = get_chart('hash-rate')      # TH/s
    time.sleep(1)                            # rate limit
    difficulty = get_chart('difficulty')     # raw difficulty

    df_h = pd.DataFrame(hashrate,   columns=['timestamp', 'network_hashrate_ths'])
    df_d = pd.DataFrame(difficulty, columns=['timestamp', 'difficulty'])

    df_h['timestamp'] = pd.to_numeric(df_h['timestamp'], errors='coerce')
    df_d['timestamp'] = pd.to_numeric(df_d['timestamp'], errors='coerce')
    df_h['network_hashrate_ths'] = pd.to_numeric(df_h['network_hashrate_ths'], errors='coerce')
    df_d['difficulty'] = pd.to_numeric(df_d['difficulty'], errors='coerce')

    df_h['date'] = pd.to_datetime(df_h['timestamp'], unit='s', errors='coerce').dt.date.astype(str)
    df_d['date'] = pd.to_datetime(df_d['timestamp'], unit='s', errors='coerce').dt.date.astype(str)

    df = df_h.merge(df_d, on='date', how='outer').sort_values('date')
    df = df[['date', 'network_hashrate_ths', 'difficulty']].dropna(subset=['network_hashrate_ths', 'difficulty'])
    df['network_hashrate_ths'] = df['network_hashrate_ths'].round(0)
    df['difficulty']           = df['difficulty'].round(0)

    # Filter to our date range
    df = df[(df['date'] >= START_DATE) & (df['date'] <= END_DATE)]

    df.to_csv('data/btc_network_data.csv', index=False)
    print(f"  Saved btc_network_data.csv   → {len(df)} rows")
    return df


# ─── 3. MINER FLEET DATASET — Synthetic (realistic) ─────────────────────────
def create_miner_dataset():
    """
    Create a realistic miner hardware dataset.
    Real-world Antminer S19 / S19 Pro / S19 XP specs used as basis.
    """
    print("Creating miner fleet dataset...")

    np.random.seed(42)

    # Hardware models (realistic ASIC specs)
    models = {
        'Antminer S19':    {'hashrate_th': 95,   'power_w': 3250, 'units': 50},
        'Antminer S19 Pro':{'hashrate_th': 110,  'power_w': 3250, 'units': 30},
        'Antminer S19 XP': {'hashrate_th': 140,  'power_w': 3010, 'units': 20},
        'Antminer S21':    {'hashrate_th': 200,  'power_w': 3500, 'units': 10},
        'Whatsminer M30S': {'hashrate_th': 90,   'power_w': 3400, 'units': 25},
    }

    rows = []
    for model, specs in models.items():
        for unit_id in range(1, specs['units'] + 1):
            # Simulate realistic hardware variance (±5%)
            eff_hashrate = specs['hashrate_th'] * np.random.uniform(0.93, 1.02)
            eff_power    = specs['power_w']     * np.random.uniform(0.97, 1.03)
            efficiency   = eff_power / eff_hashrate   # W/TH
            rows.append({
                'miner_id':         f"{model.replace(' ','_')}_{unit_id:03d}",
                'model':            model,
                'hashrate_ths':     round(eff_hashrate, 2),   # TH/s per unit
                'power_watts':      round(eff_power, 0),
                'efficiency_w_th':  round(efficiency, 2),
                'location':         np.random.choice(['Texas', 'Kentucky', 'Quebec', 'Iceland']),
                'elec_cost_kwh':    round(np.random.uniform(0.035, 0.065), 4),  # $/kWh
                'install_date':     pd.Timestamp(
                    '2022-01-01') + pd.Timedelta(days=int(np.random.uniform(0, 365))),
            })

    df = pd.DataFrame(rows)
    df['install_date'] = df['install_date'].dt.strftime('%Y-%m-%d')
    df.to_csv('data/miner_fleet.csv', index=False)
    print(f"  Saved miner_fleet.csv        → {len(df)} miners")
    return df


# ─── 4. MERGE INTO MASTER DATASET ────────────────────────────────────────────
def build_master(df_price, df_network, df_miners):
    """
    Merge price, network, and miner data into a single master table
    with pre-calculated profitability columns.
    Power BI will import this directly.
    """
    print("Building master dataset...")

    # Fleet totals
    total_hashrate_ths = df_miners['hashrate_ths'].sum()           # TH/s
    total_power_w      = df_miners['power_watts'].sum()            # Watts
    avg_elec_cost      = df_miners['elec_cost_kwh'].mean()         # $/kWh
    total_units        = len(df_miners)

    print(f"  Fleet: {total_units} miners, {total_hashrate_ths:.0f} TH/s, "
          f"{total_power_w/1e6:.2f} MW, avg ${avg_elec_cost:.4f}/kWh")

    # Merge price + network on date
    df = df_price.merge(df_network, on='date', how='inner')
    df = df.sort_values('date').reset_index(drop=True)

    # ── PROFITABILITY CALCULATIONS ──────────────────────────────────────────
    # Bitcoin block reward (accounting for halvings)
    def block_reward(date_str):
        d = datetime.strptime(date_str, '%Y-%m-%d')
        if d < datetime(2024, 4, 20):  return 6.25
        if d < datetime(2028, 3, 1):   return 3.125
        return 1.5625

    df['block_reward_btc'] = df['date'].apply(block_reward)

    # Daily BTC mined by fleet
    # Formula: (hashrate_ths * 1e12 * 86400) / (difficulty * 2^32) * block_reward * blocks_per_day
    BLOCKS_PER_DAY  = 144   # target (one every 10 min)
    SECONDS_PER_DAY = 86400
    df['blocks_per_day_expected'] = (
        (total_hashrate_ths * 1e12 * SECONDS_PER_DAY)
        / (df['difficulty'] * (2**32))
    )
    df['btc_mined_daily'] = df['blocks_per_day_expected'] * df['block_reward_btc']

    # Revenue
    df['daily_revenue_usd'] = (df['btc_mined_daily'] * df['btc_price_usd']).round(2)

    # Electricity cost
    df['daily_power_kwh']   = (total_power_w * 24 / 1000).round(2)   # kWh/day
    df['daily_elec_cost_usd'] = (df['daily_power_kwh'] * avg_elec_cost).round(2)

    # Other operational costs (pool fee 2%, misc 5%)
    df['pool_fee_usd']    = (df['daily_revenue_usd'] * 0.02).round(2)
    df['opex_other_usd']  = (df['daily_revenue_usd'] * 0.05).round(2)
    df['total_cost_usd']  = (df['daily_elec_cost_usd'] + df['pool_fee_usd'] + df['opex_other_usd']).round(2)

    # Profit metrics
    df['gross_profit_usd']  = (df['daily_revenue_usd'] - df['total_cost_usd']).round(2)
    df['profit_margin_pct'] = (df['gross_profit_usd'] / df['daily_revenue_usd'].replace(0, np.nan) * 100).round(2)
    df['is_profitable']     = (df['gross_profit_usd'] > 0).astype(int)

    # Break-even BTC price
    df['breakeven_btc_price'] = (df['total_cost_usd'] / df['btc_mined_daily'].replace(0, np.nan)).round(2)
    df['btc_premium_pct']     = ((df['btc_price_usd'] - df['breakeven_btc_price']) / df['breakeven_btc_price'] * 100).round(2)

    # ROI (annualised)
    df['roi_annualized_pct'] = (df['gross_profit_usd'] / df['total_cost_usd'].replace(0, np.nan) * 365 * 100).round(2)

    # Efficiency ratio (revenue per kWh)
    df['revenue_per_kwh'] = (df['daily_revenue_usd'] / df['daily_power_kwh']).round(4)

    # Add fleet metadata columns
    df['fleet_hashrate_ths'] = round(total_hashrate_ths, 2)
    df['fleet_power_mw']     = round(total_power_w / 1e6, 4)
    df['avg_elec_cost_kwh']  = round(avg_elec_cost, 4)
    df['total_miners']       = total_units

    # Month / Year columns for Power BI grouping
    df['year']       = pd.to_datetime(df['date']).dt.year
    df['month']      = pd.to_datetime(df['date']).dt.month
    df['month_name'] = pd.to_datetime(df['date']).dt.strftime('%b %Y')
    df['quarter']    = pd.to_datetime(df['date']).dt.to_period('Q').astype(str)

    df.to_csv('data/master_mining_data.csv', index=False)
    print(f"  Saved master_mining_data.csv → {len(df)} rows, {len(df.columns)} columns")
    print(f"\n  Sample profitability:")
    print(df[['date','btc_price_usd','daily_revenue_usd','total_cost_usd',
              'gross_profit_usd','breakeven_btc_price']].tail(5).to_string(index=False))
    return df


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 55)
    print("  Bitcoin Mining BI Dashboard — Phase 1: Data Collection")
    print("=" * 55 + "\n")

    df_price   = fetch_btc_price()
    time.sleep(2)   # respect CoinGecko rate limit

    df_network = fetch_network_data()
    df_miners  = create_miner_dataset()
    df_master  = build_master(df_price, df_network, df_miners)

    print("\n✅ All files saved to /data/")
    print("   Next step: open Power BI → Get Data → CSV → import master_mining_data.csv")
