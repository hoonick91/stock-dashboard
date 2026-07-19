"""
Stock Analysis Dashboard - Flask API Server
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from dotenv import load_dotenv
import cache_manager as cm

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

# ── 인메모리 캐시 ────────────────────────────────────────────────────────────
_cache = {}
CACHE_TTL = 300  # 5분


def cache_get(key):
    entry = _cache.get(key)
    if entry and time.time() - entry['ts'] < CACHE_TTL:
        return entry['data']
    return None


def cache_set(key, data):
    _cache[key] = {'data': data, 'ts': time.time()}


# ── API 클라이언트 팩토리 ────────────────────────────────────────────────────
def get_fmp():
    key = os.getenv('FMP_API_KEY')
    if not key:
        return None
    try:
        from fmp_api import FMPClient
        return FMPClient(api_key=key)
    except Exception:
        return None


def get_fred():
    key = os.getenv('FRED_API_KEY')
    if not key:
        return None
    try:
        from fred_api import FREDClient
        return FREDClient(api_key=key)
    except Exception:
        return None


def get_yf():
    try:
        from yf_api import YFClient
        return YFClient()
    except Exception:
        return None


# ── 데이터 수집 헬퍼 ────────────────────────────────────────────────────────
def fetch_quote(symbol):
    fmp = get_fmp()
    if fmp:
        q = fmp.get_quote(symbol)
        if q:
            return {
                'price': q.get('price'),
                'change': q.get('change'),
                'changesPercentage': q.get('changesPercentage'),
                'marketCap': q.get('marketCap'),
                'priceAvg50': q.get('priceAvg50'),
                'priceAvg200': q.get('priceAvg200'),
                'volume': q.get('volume'),
                'pe': q.get('pe'),
                'eps': q.get('eps'),
                'name': q.get('name'),
                'exchange': q.get('exchange'),
            }

    yf = get_yf()
    if yf:
        q = yf.get_quote(symbol)
        if q:
            return {
                'price': q.get('price'),
                'change': q.get('change'),
                'changesPercentage': q.get('changesPercentage'),
                'volume': q.get('volume'),
            }
    return None


def fetch_ttm_ratios(symbol):
    fmp = get_fmp()
    if fmp:
        result = {}
        # key-metrics-ttm: ROE, ROA
        m = fmp.get_key_metrics(symbol)
        if m:
            result['roe'] = m.get('returnOnEquityTTM')
            result['roa'] = m.get('returnOnAssetsTTM')
        # ratios-ttm: PE, PEG, PB, debt/equity
        r = fmp.get_ratios(symbol, period='ttm')
        if r is not None and not r.empty:
            row = r.iloc[0].to_dict()
            result['peRatio'] = row.get('priceToEarningsRatioTTM')
            result['pegRatio'] = row.get('priceToEarningsGrowthRatioTTM')
            result['pbRatio'] = row.get('priceToBookRatioTTM')
            result['debtToEquity'] = row.get('debtToEquityRatioTTM')
        return result

    yf = get_yf()
    if yf:
        fin = yf.get_financials(symbol)
        if fin:
            return {
                'peRatio': fin.get('pe_ratio'),
                'pegRatio': fin.get('peg_ratio'),
                'pbRatio': fin.get('pb_ratio'),
                'roe': fin.get('roe'),
            }
    return {}


def fetch_income_statement(symbol, period, limit):
    fmp = get_fmp()
    if fmp:
        data = fmp.get_income_statement(symbol, period=period, limit=limit)
        if data:
            return data
    return []


def fetch_balance_sheet(symbol, period, limit):
    fmp = get_fmp()
    if fmp:
        data = fmp.get_balance_sheet(symbol, period=period, limit=limit)
        if data:
            return data
    return []


def fetch_financial_growth(symbol, period, limit):
    fmp = get_fmp()
    if fmp:
        data = fmp.get_financial_growth(symbol, period=period, limit=limit)
        if data:
            return data
    return []


def fetch_rsi(symbol, timeframe='daily'):
    fmp = get_fmp()
    if fmp:
        df = fmp.get_technical_indicator(symbol, 'rsi', 14, limit=30, timeframe=timeframe)
        if df is not None and not df.empty:
            return [
                {'date': str(row['date'])[:10], 'rsi': round(float(row['rsi']), 2)}
                for _, row in df.iterrows()
            ]

    yf = get_yf()
    if yf:
        df = yf.calculate_rsi(symbol, 14, days=30)
        if df is not None and not df.empty:
            result = []
            for _, row in df.iterrows():
                rsi_val = row['rsi']
                if rsi_val == rsi_val:
                    result.append({'date': str(row['date'])[:10], 'rsi': round(float(rsi_val), 2)})
            return result
    return []


def fetch_sma(symbol, period, timeframe='daily'):
    fmp = get_fmp()
    if fmp:
        df = fmp.get_technical_indicator(symbol, 'sma', period, limit=60, timeframe=timeframe)
        if df is not None and not df.empty:
            return [
                {
                    'date': str(row['date'])[:10],
                    'sma': round(float(row['sma']), 2),
                    'close': round(float(row['close']), 2),
                }
                for _, row in df.iterrows()
            ]

    yf = get_yf()
    if yf:
        df = yf.calculate_sma(symbol, period, days=60)
        if df is not None and not df.empty:
            col = f'sma_{period}'
            result = []
            for _, row in df.iterrows():
                val = row[col]
                if val == val:
                    result.append({
                        'date': str(row['date'])[:10],
                        'sma': round(float(val), 2),
                        'close': round(float(row['close']), 2),
                    })
            return result
    return []


def fetch_technicals_yf(symbol, timeframe):
    """주봉/월봉: yfinance로 RSI(14), SMA50, SMA200 직접 계산"""
    try:
        import yfinance as yf_lib
        import pandas as pd

        cfg = {
            'weekly':  ('1wk', '10y'),
            'monthly': ('1mo', '20y'),
        }
        interval, hist_period = cfg[timeframe]
        df = yf_lib.Ticker(symbol).history(period=hist_period, interval=interval)
        if df is None or df.empty:
            return [], [], []

        df = df[['Close']].copy()
        df['sma50']  = df['Close'].rolling(50).mean()
        df['sma200'] = df['Close'].rolling(200).mean()

        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        df = df.dropna(subset=['sma50', 'rsi']).tail(60)
        dates = [str(d)[:10] for d in df.index]

        rsi_data  = [{'date': d, 'rsi': round(float(r), 2)}
                     for d, r in zip(dates, df['rsi'])]
        sma50_data = [{'date': d, 'sma': round(float(s), 2), 'close': round(float(c), 2)}
                      for d, s, c in zip(dates, df['sma50'], df['Close'])]
        sma200_data = [{'date': d, 'sma': round(float(s), 2), 'close': round(float(c), 2)}
                       for d, s, c in zip(dates, df['sma200'], df['Close'])
                       if s == s]

        return rsi_data, sma50_data, sma200_data
    except Exception as e:
        print(f"yfinance {timeframe} 기술지표 계산 실패 ({symbol}): {e}")
        return [], [], []


def build_roe_chart(income_data, balance_data):
    balance_by_date = {b['date']: b for b in (balance_data or [])}
    result = []
    for inc in (income_data or []):
        date = inc.get('date', '')
        net_income = inc.get('netIncome', 0) or 0
        bal = balance_by_date.get(date, {})
        equity = bal.get('totalStockholdersEquity') or bal.get('stockholdersEquity', 0) or 0
        if equity != 0:
            result.append({
                'date': date,
                'roe': round(net_income / equity * 100, 2),
                'netIncome': net_income,
                'equity': equity,
            })
    return result


MACRO_SERIES = {
    'VIX': 'VIXCLS',
    '10Y_Treasury': 'DGS10',
    'FCI': 'NFCI',
    'HY_Spread': 'BAMLH0A0HYM2',
    'Dollar_Index': 'DTWEXBGS',
}


def _yf_price(yf_client, ticker):
    try:
        import yfinance as yf_lib
        t = yf_lib.Ticker(ticker)
        info = t.fast_info
        price = getattr(info, 'last_price', None) or getattr(info, 'regular_market_price', None)
        return price
    except Exception:
        return None


def fetch_macro():
    fred = get_fred()
    result = {}
    if fred:
        for name, series_id in MACRO_SERIES.items():
            val = fred.get_latest_value(series_id)
            if val:
                result[name] = val
    else:
        # FRED 키 없으면 yfinance로 가능한 지표 수집
        today = datetime.now().strftime('%Y-%m-%d')
        yf_map = {
            'VIX': '^VIX',
            '10Y_Treasury': '^TNX',
            'Dollar_Index': 'DX-Y.NYB',
        }
        for name, ticker in yf_map.items():
            price = _yf_price(None, ticker)
            if price:
                result[name] = {'value': round(price, 2), 'date': today}

    # S&P500 종목 중 200일 이평선 상회 비중 (FMP)
    fmp = get_fmp()
    if fmp:
        pct = fmp.get_market_breadth_ma200()
        if pct is not None:
            result['Above_MA200'] = {'value': pct, 'date': datetime.now().strftime('%Y-%m-%d')}

    return result


# ── 캐시 래퍼 ────────────────────────────────────────────────────────────────

def _cached_macro():
    data = cm.get_macro()
    if data is None:
        print('[API] macro 조회')
        data = fetch_macro()
        cm.set_macro(data)
    return data


def _cached_quote(symbol):
    data = cm.get_quote(symbol)
    if data is None:
        print(f'[API] {symbol} quote 조회')
        data = fetch_quote(symbol)
        if data:
            cm.set_quote(symbol, data)
    return data


def _cached_ttm(symbol):
    data = cm.get_ttm(symbol)
    if data is None:
        print(f'[API] {symbol} ttm 조회')
        data = fetch_ttm_ratios(symbol)
        cm.set_ttm(symbol, data)
    return data


def _cached_financials(symbol, period):
    data = cm.get_financials(symbol, period)
    if data is None:
        print(f'[API] {symbol} financials/{period} 조회')
        limit = 5 if period == 'annual' else 8
        income  = fetch_income_statement(symbol, period, limit)
        balance = fetch_balance_sheet(symbol, period, limit)
        growth  = fetch_financial_growth(symbol, period, limit)
        roe     = build_roe_chart(income, balance)
        data = {'income': income, 'balance': balance, 'growth': growth, 'roe': roe}
        cm.set_financials(symbol, period, data)
    return data


def _cached_technicals(symbol, timeframe):
    cached = cm.get_technicals(symbol, timeframe)
    if cached:
        return cached['rsi'], cached['sma50'], cached['sma200']
    print(f'[API] {symbol} technicals/{timeframe} 조회')
    if timeframe in ('weekly', 'monthly'):
        rsi, sma50, sma200 = fetch_technicals_yf(symbol, timeframe)
    else:
        rsi   = fetch_rsi(symbol, timeframe)
        sma50  = fetch_sma(symbol, 50, timeframe)
        sma200 = fetch_sma(symbol, 200, timeframe)
    cm.set_technicals(symbol, timeframe, rsi, sma50, sma200)
    return rsi, sma50, sma200


# ── 라우트 ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    html_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'dashboard_v3_ui.html')
    )
    if os.path.exists(html_path):
        return send_file(html_path)
    return '<h1>Stock Dashboard</h1><p>dashboard_v3_ui.html not found</p>'


@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'ok',
        'fmp': bool(os.getenv('FMP_API_KEY')),
        'fred': bool(os.getenv('FRED_API_KEY')),
        'time': datetime.now().isoformat(),
    })


@app.route('/api/stock/<symbol>')
def get_stock(symbol):
    symbol = symbol.upper()
    key = f'stock:{symbol}'
    hit = cache_get(key)
    if hit:
        return jsonify(hit)

    quote = _cached_quote(symbol)
    if not quote:
        return jsonify({'error': f'종목을 찾을 수 없습니다: {symbol}'}), 404

    ttm     = _cached_ttm(symbol)
    annual  = _cached_financials(symbol, 'annual')
    quarter = _cached_financials(symbol, 'quarter')
    rsi, sma50, sma200 = _cached_technicals(symbol, 'daily')

    data = {
        'symbol': symbol,
        'generated_at': datetime.now().isoformat(),
        'quote': quote,
        'financials': {
            'ttm': ttm,
            'annual': {
                'income':  annual.get('income', []),
                'balance': annual.get('balance', []),
                'growth':  annual.get('growth', []),
            },
            'quarter': {
                'income':  quarter.get('income', []),
                'balance': quarter.get('balance', []),
                'growth':  quarter.get('growth', []),
            },
        },
        'charts': {
            'roe_annual':  annual.get('roe', []),
            'roe_quarter': quarter.get('roe', []),
            'rsi':   rsi,
            'sma50':  sma50,
            'sma200': sma200,
        },
    }
    cache_set(key, data)
    return jsonify(data)


@app.route('/api/stock/<symbol>/quote')
def get_quote(symbol):
    symbol = symbol.upper()
    key = f'quote:{symbol}'
    hit = cache_get(key)
    if hit:
        return jsonify(hit)

    quote = fetch_quote(symbol)
    if not quote:
        return jsonify({'error': f'종목을 찾을 수 없습니다: {symbol}'}), 404

    data = {'symbol': symbol, **quote}
    cache_set(key, data)
    return jsonify(data)


@app.route('/api/stock/<symbol>/financials')
def get_financials(symbol):
    symbol = symbol.upper()
    period = request.args.get('period', 'annual')
    limit = int(request.args.get('limit', 5 if period == 'annual' else 8))

    key = f'financials:{symbol}:{period}:{limit}'
    hit = cache_get(key)
    if hit:
        return jsonify(hit)

    income = fetch_income_statement(symbol, period, limit)
    balance = fetch_balance_sheet(symbol, period, limit)
    growth = fetch_financial_growth(symbol, period, limit) if period == 'annual' else []

    data = {
        'symbol': symbol,
        'period': period,
        'income': income,
        'balance': balance,
        'growth': growth,
    }
    cache_set(key, data)
    return jsonify(data)


@app.route('/api/stock/<symbol>/technicals')
def get_technicals(symbol):
    symbol = symbol.upper()
    timeframe = request.args.get('timeframe', 'daily')
    if timeframe not in ('daily', 'weekly', 'monthly'):
        timeframe = 'daily'

    key = f'technicals:{symbol}:{timeframe}'
    hit = cache_get(key)
    if hit:
        return jsonify(hit)

    rsi, sma50, sma200 = _cached_technicals(symbol, timeframe)
    quote = _cached_quote(symbol)
    price = quote['price'] if quote else None

    divergence_50  = round(price / sma50[-1]['sma']  * 100, 2) if price and sma50  else None
    divergence_200 = round(price / sma200[-1]['sma'] * 100, 2) if price and sma200 else None

    data = {
        'symbol': symbol,
        'timeframe': timeframe,
        'rsi': rsi,
        'sma50': sma50,
        'sma200': sma200,
        'divergence_50': divergence_50,
        'divergence_200': divergence_200,
    }
    cache_set(key, data)
    return jsonify(data)


@app.route('/api/macro')
def get_macro():
    key = 'macro'
    hit = cache_get(key)
    if hit:
        return jsonify(hit)

    data = _cached_macro()
    cache_set(key, data)
    return jsonify(data)


def _parse_ua(ua):
    import re
    device = '모바일' if any(x in ua for x in ['Mobile', 'Android', 'iPhone', 'iPad']) else '데스크톱'
    if 'iPhone' in ua or 'iPad' in ua:
        os_name = 'iOS'
    elif 'Android' in ua:
        os_name = 'Android'
    elif 'Mac OS X' in ua:
        os_name = 'macOS'
    elif 'Windows' in ua:
        os_name = 'Windows'
    elif 'Linux' in ua:
        os_name = 'Linux'
    else:
        os_name = '기타'
    if 'Edg/' in ua:
        browser, m = 'Edge', re.search(r'Edg/(\d+)', ua)
    elif 'Chrome/' in ua:
        browser, m = 'Chrome', re.search(r'Chrome/(\d+)', ua)
    elif 'Firefox/' in ua:
        browser, m = 'Firefox', re.search(r'Firefox/(\d+)', ua)
    elif 'Safari/' in ua:
        browser, m = 'Safari', re.search(r'Version/(\d+)', ua)
    else:
        browser, m = '기타', None
    return device, os_name, browser


def _get_city(ip):
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=3)
        d = r.json()
        if d.get('status') == 'success':
            return d.get('city', '')
    except Exception:
        pass
    return ''


def _send_discord(msg):
    import requests as _req
    webhook = os.getenv('DISCORD_WEBHOOK')
    if not webhook:
        print('[Discord] 웹훅 URL 없음')
        return
    try:
        r = _req.post(webhook, json={'content': msg}, timeout=5)
        print(f'[Discord] 전송 완료: {r.status_code}')
    except Exception as e:
        print(f'[Discord] 전송 실패: {e}')


@app.route('/api/log', methods=['POST'])
def log_event():
    import threading
    data = request.get_json() or {}
    symbol = data.get('symbol', '?').upper()
    ua = data.get('userAgent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    ip = ip.split(',')[0].strip()

    def _notify():
        device, os_name, browser = _parse_ua(ua)
        city = _get_city(ip)
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        parts = [f'**{symbol}**', f'{device} · {os_name} · {browser}']
        if city:
            parts.append(city)
        parts.append(now)
        _send_discord(' | '.join(parts))

    threading.Thread(target=_notify, daemon=True).start()
    return jsonify({'ok': True})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    print(f'Stock Dashboard 시작: http://localhost:{port}')
    print(f'  FMP API: {"✓" if os.getenv("FMP_API_KEY") else "✗ (yfinance 폴백)"}')
    print(f'  FRED API: {"✓" if os.getenv("FRED_API_KEY") else "✗ (VIX만 제공)"}')
    app.run(host='0.0.0.0', port=port, debug=debug)
