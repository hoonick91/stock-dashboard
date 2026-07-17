# 모니터링 지표 API 수집 가이드

주식 투자 모니터링 지표를 API로 자동 수집하는 방법

**관련 문서**: [[모니터링 지표]] - 각 지표의 상세 설명

---

## API 사용 가능 지표 요약

| 지표           | API              | 가능 여부 | 비고                 |
| ------------ | ---------------- | ----- | ------------------ |
| **유동성**      |                  |       |                    |
| 미국 국채 10년물   | FRED             | ✅     | DGS10              |
| 달러 환율        | FRED/FMP/Massive | ✅     | DTWEXBGS, FX API   |
| FCI          | FRED             | ✅     | NFCI               |
| **차트(심리)**   |                  |       |                    |
| 이동평균선        | FMP/Massive      | ✅     | SMA/EMA            |
| 이평선상회 비중     | FMP/Massive      | ⚠️    | 직접 계산 필요           |
| 이격도          | FMP/Massive      | ⚠️    | 가격+이평선 조합          |
| RSI          | FMP/Massive      | ✅     | RSI                |
| M자/W자 패턴     | -                | ❌     | 수동 분석              |
| CUP & Handle | -                | ❌     | 수동 분석              |
| **실적**       |                  |       |                    |
| PER          | FMP/Massive      | ✅     | Ratios/Key Metrics |
| PEG          | FMP              | ✅     | Key Metrics        |
| **역발상**      |                  |       |                    |
| 낙관/비관지수      | -                | ❌     | 웹 스크래핑             |
| Put/Call     | Massive          | ✅     | Options API        |
| Margin Debt  | FRED             | ⚠️    | 월간, 지연             |
| 하이일드         | FRED             | ✅     | BAMLH0A0HYM2       |
| VIX          | FRED             | ✅     | VIXCLS             |
| 언론/댓글        | -                | ❌     | NLP 필요             |

**범례**:
- ✅ API로 직접 조회 가능
- ⚠️ 조합/계산 필요 또는 제한적
- ❌ API 제공 안 됨

**결과**: 17개 지표 중 **10개 직접 가능**, 3개 조합 가능, 4개 불가

---

## API 개요

### 1. FRED API (Federal Reserve Economic Data)
- **제공**: 미국 연방준비은행 세인트루이스 지점
- **데이터**: 거시경제, 금리, 환율, 금융지표
- **가격**: 무료
- **API 키**: https://fred.stlouisfed.org/docs/api/api_key.html
- **문서**: https://fred.stlouisfed.org/docs/api/fred/

### 2. Financial Modeling Prep API
- **제공**: FMP
- **데이터**: 주가, 재무제표, 기술지표, 밸류에이션
- **가격**: 무료 (250 requests/day), 유료 플랜
- **API 키**: https://site.financialmodelingprep.com/developer/docs
- **문서**: https://site.financialmodelingprep.com/developer/docs

### 3. Massive API
- **제공**: Massive.com
- **데이터**: 실시간/역사적 주가, 기술지표, 재무비율, 옵션 데이터, 공매도 정보
- **가격**: 무료 플랜, 유료 플랜 (real-time)
- **문서**:
  - 개요: https://massive.com/stocks
  - REST API: https://massive.com/docs/rest/stocks/overview
  - 옵션: https://massive.com/options
- **특징**:
  - 19개 주요 거래소 + 다크풀 + OTC
  - 20년+ 역사적 데이터
  - WebSocket 실시간 스트리밍
  - 나노초 단위 정밀도

---

## 지표별 API 매핑

### ✅ 1. 유동성 지표

#### 1.1 미국 국채 10년물 금리
**API**: FRED
**시리즈 코드**: `DGS10`
**엔드포인트**:
```
https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=YOUR_API_KEY&file_type=json
```

**응답 예시**:
```json
{
  "observations": [
    {
      "date": "2026-06-25",
      "value": "4.25"
    }
  ]
}
```

**활용**: 일간 금리 데이터, 최근 30일 추이 확인

---

#### 1.2 달러 환율
**API**: FRED
**시리즈 코드**:
- `DTWEXBGS` - 달러 인덱스 (Broad, 월간)
- `DEXUSEU` - 달러/유로 환율 (일간)

**엔드포인트**:
```
https://api.stlouisfed.org/fred/series/observations?series_id=DTWEXBGS&api_key=YOUR_API_KEY&file_type=json
```

**주의**: DTWEXBGS는 월간 업데이트

**대안**: Financial Modeling Prep에서 실시간 환율
```
https://financialmodelingprep.com/api/v3/fx/EURUSD?apikey=YOUR_API_KEY
```

---

#### 1.3 금융상황지수 (FCI)
**API**: FRED
**시리즈 코드**: `NFCI` (Chicago Fed National Financial Conditions Index)

**엔드포인트**:
```
https://api.stlouisfed.org/fred/series/observations?series_id=NFCI&api_key=YOUR_API_KEY&file_type=json
```

**해석**:
- 양수(+): 긴축
- 음수(-): 완화
- 주간 업데이트

**추가 지표**:
- `ANFCI` - Adjusted NFCI
- `NFCICREDIT` - Credit Subindex
- `NFCINONFINLEVERAGE` - Leverage Subindex

---

### ✅ 2. 차트(심리) 지표

#### 2.1 이동평균선
**API**: Financial Modeling Prep
**엔드포인트**:
```
https://financialmodelingprep.com/api/v3/technical_indicator/daily/AAPL?period=50&type=sma&apikey=YOUR_API_KEY
```

**파라미터**:
- `type`: `sma` (단순), `ema` (지수), `wma` (가중)
- `period`: 5, 20, 50, 60, 120, 200

**응답 예시**:
```json
[
  {
    "date": "2026-06-25",
    "close": 180.50,
    "sma": 175.20
  }
]
```

**활용**: 50일/200일 이평선 계산 후 이격도 직접 계산
```
이격도 = (close / sma) × 100
```

---

#### 2.2 이평선상회 종목 비중
**API**: 직접 계산 필요
**방법**:
1. FMP에서 시장 전체 종목 리스트 가져오기
```
https://financialmodelingprep.com/api/v3/stock/list?apikey=YOUR_API_KEY
```

2. 각 종목의 20일선 상회 여부 확인
3. 비율 계산

**한계**: API 호출 제한으로 대량 종목 처리 어려움

---

#### 2.3 이격도
**API**: Financial Modeling Prep
**방법**: 현재가 + 이동평균 조합

1. 현재가 조회:
```
https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=YOUR_API_KEY
```

2. 50일/200일 이평선:
```
https://financialmodelingprep.com/api/v3/technical_indicator/daily/AAPL?period=50&type=sma&apikey=YOUR_API_KEY
```

3. 이격도 계산:
```python
divergence = (current_price / sma_50) * 100
```

---

#### 2.4 RSI
**API**: Financial Modeling Prep
**엔드포인트**:
```
https://financialmodelingprep.com/api/v3/technical_indicator/daily/AAPL?period=14&type=rsi&apikey=YOUR_API_KEY
```

**응답 예시**:
```json
[
  {
    "date": "2026-06-25",
    "rsi": 67.5
  }
]
```

**활용**: 70 이상 과매수, 30 이하 과매도

---

#### 2.5~2.6 차트 패턴 (M자/W자, CUP & Handle)
**API**: ❌ 제공 안 됨
**대안**:
- 주가 데이터 받아서 직접 패턴 인식 알고리즘 구현
- TradingView 등 차트 플랫폼에서 수동 확인

---

### ✅ 3. 적정주가(실적) 지표

#### 3.1 PER (Price to Earnings Ratio)
**API**: Financial Modeling Prep
**엔드포인트**:
```
https://financialmodelingprep.com/api/v3/ratios/AAPL?apikey=YOUR_API_KEY
```

**응답 예시**:
```json
[
  {
    "symbol": "AAPL",
    "date": "2024-12-31",
    "priceEarningsRatio": 28.5,
    "priceToBookRatio": 45.2,
    "returnOnEquity": 1.47
  }
]
```

**추가 밸류에이션 지표**:
- Key Metrics API:
```
https://financialmodelingprep.com/api/v3/key-metrics/AAPL?apikey=YOUR_API_KEY
```

응답에 포함:
- PE Ratio
- PEG Ratio
- EPS
- Market Cap

---

#### 3.2 PEG
**API**: Financial Modeling Prep
**엔드포인트**: 위와 동일 (Key Metrics API)

**수동 계산**:
```
PEG = PE Ratio / 예상 성장률(%)
```

**성장률 데이터**:
```
https://financialmodelingprep.com/api/v3/financial-growth/AAPL?apikey=YOUR_API_KEY
```

---

### ✅ 4. 역발상(위기/기회) 지표

#### 4.1 낙관/비관지수
**API**: ❌ FRED/FMP에서 직접 제공 안 됨
**대안**:
- CNN Fear & Greed Index: 웹 스크래핑 필요
- AAII Sentiment Survey: 유료 데이터

---

#### 4.2 Put/Call 지표
**API**: Massive API
**엔드포인트**: Options API - Option Chain Snapshot
**문서**:
- 개요: https://massive.com/options
- API 문서: https://massive.com/docs/rest/options/overview
- 가격: https://massive.com/pricing?product=options

**필요한 데이터**:
1. **Option Chain Snapshot** (옵션 체인 스냅샷)
   - 특정 종목의 모든 옵션 계약 정보
   - 각 계약의 type (call/put)
   - Volume (거래량)
   - Open Interest (미결제약정)

2. **포함 데이터 필드**:
   - Contract type: Call or Put
   - Strike price (행사가)
   - Expiration date (만기일)
   - Volume (거래량) ← **Put/Call Ratio 계산에 필수**
   - Open Interest (미결제약정)
   - Greeks: Delta, Gamma, Theta, Vega
   - Implied Volatility (내재변동성)
   - Premium (프리미엄)

**플랜 선택**:
- **무료/기본 플랜**: 15분 지연 데이터 (Put/Call Ratio에는 충분)
- **유료 플랜**: 실시간 데이터
- **Business 플랜**: Fair Market Value + 거래소 보고 요구사항 면제

**엔드포인트 예시**:
```
GET /v1/options/{symbol}/chain/snapshot
```

**Put/Call Ratio 계산 방법**:
```python
# 1. 옵션 체인 스냅샷 조회
response = get_options_chain("SPY")  # S&P 500 ETF

# 2. Put/Call 거래량 합계
put_volume = sum([contract['volume'] for contract in response
                  if contract['type'] == 'put'])
call_volume = sum([contract['volume'] for contract in response
                   if contract['type'] == 'call'])

# 3. Ratio 계산
put_call_ratio = put_volume / call_volume

# 해석:
# - 1.0 이상: Put 거래 많음 → 하락 베팅 (공포)
# - 0.7 이하: Call 거래 많음 → 상승 베팅 (과열)
```

**실전 활용**:
- **일간 체크**: S&P 500 (SPY) 또는 QQQ의 Put/Call Ratio
- **극단값 확인**:
  - 1.2 이상 → 극심한 공포 → 역발상 매수 신호
  - 0.5 이하 → 극도의 낙관 → 조정 경계

**대안**:
- CBOE 공식 데이터: http://www.cboe.com/data/ (무료, 지연)
- Massive API가 가장 포괄적이고 API 친화적

---

#### 4.3 Margin Debt (신용융자 잔고)
**API**: FRED (부분적)
**시리즈 코드**: 검색 필요 (FINRA 데이터는 월간 발표)

**대안**:
- FINRA 공식 사이트에서 월간 리포트 다운로드
- 웹 스크래핑

---

#### 4.4 하이일드 스프레드
**API**: FRED
**시리즈 코드**: `BAMLH0A0HYM2`
**엔드포인트**:
```
https://api.stlouisfed.org/fred/series/observations?series_id=BAMLH0A0HYM2&api_key=YOUR_API_KEY&file_type=json
```

**설명**: ICE BofA US High Yield Index Option-Adjusted Spread

**응답 예시**:
```json
{
  "observations": [
    {
      "date": "2026-06-25",
      "value": "3.85"
    }
  ]
}
```

**단위**: % (퍼센트 포인트), 즉 385bp

---

#### 4.5 공포지수 (VIX)
**API**: FRED
**시리즈 코드**: `VIXCLS`
**엔드포인트**:
```
https://api.stlouisfed.org/fred/series/observations?series_id=VIXCLS&api_key=YOUR_API_KEY&file_type=json
```

**응답 예시**:
```json
{
  "observations": [
    {
      "date": "2026-06-24",
      "value": "15.20"
    }
  ]
}
```

**주의**: 영업일 기준 일간 업데이트 (주말/휴일 제외)

---

#### 4.6 언론/댓글지표
**API**: ❌ 제공 안 됨
**대안**:
- News API로 뉴스 헤드라인 수집 후 감성 분석
- Reddit/트위터 API로 소셜 미디어 분석
- 별도 NLP 모델 필요

---

## 실전 구현 예시

### Python 코드 샘플

#### FRED API 사용
```python
import requests
import pandas as pd

FRED_API_KEY = "your_fred_api_key"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

def get_fred_data(series_id, start_date="2024-01-01"):
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    df = pd.DataFrame(data["observations"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])

    return df

# 사용 예시
vix_data = get_fred_data("VIXCLS")
treasury_10y = get_fred_data("DGS10")
hy_spread = get_fred_data("BAMLH0A0HYM2")
fci = get_fred_data("NFCI")

print(f"최신 VIX: {vix_data.iloc[-1]['value']}")
print(f"최신 10년물: {treasury_10y.iloc[-1]['value']}%")
print(f"최신 HY 스프레드: {hy_spread.iloc[-1]['value']}%")
print(f"최신 FCI: {fci.iloc[-1]['value']}")
```

#### FMP API 사용
```python
import requests

FMP_API_KEY = "your_fmp_api_key"

def get_stock_quote(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
    params = {"apikey": FMP_API_KEY}
    response = requests.get(url, params=params)
    return response.json()[0]

def get_technical_indicator(symbol, indicator_type="rsi", period=14):
    url = f"https://financialmodelingprep.com/api/v3/technical_indicator/daily/{symbol}"
    params = {
        "type": indicator_type,
        "period": period,
        "apikey": FMP_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()

def get_key_metrics(symbol):
    url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}"
    params = {"apikey": FMP_API_KEY}
    response = requests.get(url, params=params)
    return response.json()[0]

# 사용 예시
aapl_quote = get_stock_quote("AAPL")
aapl_rsi = get_technical_indicator("AAPL", "rsi", 14)
aapl_sma_50 = get_technical_indicator("AAPL", "sma", 50)
aapl_metrics = get_key_metrics("AAPL")

current_price = aapl_quote["price"]
sma_50_value = aapl_sma_50[0]["sma"]
divergence = (current_price / sma_50_value) * 100

print(f"현재가: ${current_price}")
print(f"50일 이평: ${sma_50_value}")
print(f"50일 이격도: {divergence:.2f}%")
print(f"RSI: {aapl_rsi[0]['rsi']}")
print(f"PER: {aapl_metrics['peRatio']}")
print(f"PEG: {aapl_metrics.get('pegRatio', 'N/A')}")
```

#### Massive API 사용
```python
import requests

MASSIVE_API_KEY = "your_massive_api_key"
BASE_URL = "https://api.massive.com/v1"

def get_stock_data(symbol):
    """주가 및 기본 정보 조회"""
    url = f"{BASE_URL}/stocks/{symbol}/quote"
    headers = {"Authorization": f"Bearer {MASSIVE_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_technical_indicators(symbol, indicator="sma", period=50):
    """기술 지표 조회"""
    url = f"{BASE_URL}/stocks/{symbol}/indicators/{indicator}"
    headers = {"Authorization": f"Bearer {MASSIVE_API_KEY}"}
    params = {"period": period}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def get_financial_ratios(symbol):
    """재무 비율 (PER, PBR 등)"""
    url = f"{BASE_URL}/stocks/{symbol}/ratios"
    headers = {"Authorization": f"Bearer {MASSIVE_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_options_data(symbol):
    """옵션 데이터 (Put/Call 계산용)"""
    url = f"{BASE_URL}/options/{symbol}/chain"
    headers = {"Authorization": f"Bearer {MASSIVE_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.json()

# 사용 예시
aapl_quote = get_stock_data("AAPL")
aapl_sma = get_technical_indicators("AAPL", "sma", 50)
aapl_ratios = get_financial_ratios("AAPL")
aapl_options = get_options_data("AAPL")

# Put/Call Ratio 계산
total_put_volume = sum([opt['volume'] for opt in aapl_options if opt['type'] == 'put'])
total_call_volume = sum([opt['volume'] for opt in aapl_options if opt['type'] == 'call'])
put_call_ratio = total_put_volume / total_call_volume

print(f"현재가: ${aapl_quote['price']}")
print(f"50일 이평: ${aapl_sma['value']}")
print(f"PER: {aapl_ratios['pe_ratio']}")
print(f"Put/Call Ratio: {put_call_ratio:.2f}")
```

**주의**: Massive API의 실제 엔드포인트 구조는 공식 문서를 확인하세요. 위 코드는 일반적인 패턴 예시입니다.

---

## 데이터 수집 전략

### 일간 모니터링 (매일 장마감 후)
```python
# 1. 유동성 지표
treasury_10y = get_fred_data("DGS10", days=30)
vix = get_fred_data("VIXCLS", days=30)
hy_spread = get_fred_data("BAMLH0A0HYM2", days=30)

# 2. 보유 종목 기술지표
for symbol in ["AAPL", "MSFT", "NVDA"]:
    quote = get_stock_quote(symbol)
    rsi = get_technical_indicator(symbol, "rsi")
    sma_50 = get_technical_indicator(symbol, "sma", 50)
    # 저장 또는 알림
```

### 주간 모니터링 (매주 월요일)
```python
# FCI (주간 업데이트)
nfci = get_fred_data("NFCI", days=90)

# 보유 종목 밸류에이션 체크
for symbol in portfolio:
    metrics = get_key_metrics(symbol)
    check_valuation(metrics)
```

### 월간 모니터링 (월초)
```python
# 달러 인덱스 (월간)
dollar_index = get_fred_data("DTWEXBGS", days=365)

# 재무제표 업데이트 확인
for symbol in portfolio:
    financials = get_financial_statements(symbol)
    update_dcf_model(financials)
```

---

## 주의사항

### API 제한
1. **FRED**: 무료, 제한 없음 (합리적 사용)
2. **FMP 무료**: 250 requests/day
   - 종목 5개 × 지표 3개 × 일간 = 15 requests/day
   - 250개 한도면 충분

### 데이터 지연
- FRED: 영업일 기준 익일 오전 업데이트
- FMP: 실시간~15분 지연 (플랜별 차이)
- 주말/휴일: 데이터 없음 → 에러 처리 필요

### 백업 전략
- API 장애 대비 로컬 캐싱
- 마지막 성공 데이터 저장
- 여러 API 조합 (FRED 다운 시 Yahoo Finance 대체 등)

---

## 다음 단계

1. **API 키 발급**
   - FRED: https://fred.stlouisfed.org/docs/api/api_key.html
   - FMP: https://site.financialmodelingprep.com/developer/docs

2. **자동화 스크립트 작성**
   - Python/Node.js로 일간 수집 크론잡
   - 데이터베이스 저장 (SQLite, PostgreSQL)
   - 대시보드 구성 (Grafana, Streamlit)

3. **알림 시스템 구축**
   - VIX > 30 → 공포 매수 알림
   - HY Spread > 700bp → 위험 경고
   - 이격도 110% → 차익실현 고려

4. **분석 자동화**
   - 여러 지표 조합 신호
   - 백테스팅
   - 포트폴리오 리밸런싱 제안
