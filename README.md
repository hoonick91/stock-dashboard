# Stock Analysis Dashboard

주식 재무 데이터 분석 및 시각화 대시보드

## 프로젝트 개요

재무제표 기반 심층 분석을 제공하는 주식 대시보드입니다. FMP API를 활용해 기간별 PEG, ROE 등을 상세하게 분석하고, 계산 근거를 투명하게 제공합니다.

## 주요 기능

### ✅ 완료된 기능
- **거시경제 지표 모니터링**: VIX, 10Y Treasury, FCI, HY Spread, Dollar Index, Margin Debt, Above MA(200)
- **종목 분석**: 현재가, 이평선, RSI, 시가총액
- **재무 데이터 수집**:
  - 연간/분기별 손익계산서, 대차대조표, 성장률
  - TTM 기준 PEG, ROE, P/E
- **UI 설계**: 4개 탭 구조 (개요, 재무, 기술적 분석, 밸류에이션)
- **기간별 필터**: 재무(TTM/연간/분기), 가격(일봉/주봉/월봉)

### 🎨 UI 구조
```
📊 Stock Dashboard
├── 헤더 (종목 검색창)
├── 거시경제 배너 (7개 지표)
└── 메인 대시보드
    ├── [개요] 탭: 핵심 지표, 차트, RSI
    ├── [재무] 탭: ROE/손익계산서/대차대조표 (연간/분기/TTM)
    ├── [기술적 분석] 탭: RSI, 이평선 (일봉/주봉/월봉)
    └── [밸류에이션] 탭: PEG, 성장률 분석
```

## 기술 스택

### Backend (진행 중)
- Python 3.9+
- Flask (API 서버)
- pandas (데이터 처리)

### Frontend
- HTML5 / CSS3 / JavaScript
- Chart.js (차트 라이브러리)
- 반응형 디자인

### APIs
- **FMP (Financial Modeling Prep)** - 재무제표, 비율
- **FRED (Federal Reserve Economic Data)** - 거시경제 지표
- **Alpha Vantage** - RSI 기술적 지표

## 프로젝트 구조

```
llm-wiki/
├── scripts/
│   ├── fmp_api.py                    # FMP API 클라이언트 ✅
│   ├── fred_api.py                   # FRED API 클라이언트 ✅
│   ├── alphavantage_api.py           # Alpha Vantage 클라이언트 ✅
│   ├── daily_monitor.py              # 종목 모니터링 스크립트 ✅
│   ├── generate_dashboard_v2.py      # 대시보드 생성기 v2 ✅
│   └── flask_server.py               # Flask API 서버 (작업 예정)
├── data/
│   ├── dashboard_v3_ui.html          # UI 프로토타입 ✅
│   └── stock_data_NVDA.json          # 테스트 데이터 ✅
└── README.md
```

## 📋 다음 작업 단계 (Flask 서버 구축)

### Phase 1: Flask 서버 기본 구조
- [ ] `scripts/flask_server.py` 생성
- [ ] CORS 설정
- [ ] 기본 라우트 구성
  ```python
  GET /api/stock/<symbol>          # 전체 데이터 조회
  GET /api/stock/<symbol>/quote    # 현재가 조회
  GET /api/stock/<symbol>/financials?period=annual  # 재무제표
  GET /api/macro                   # 거시경제 지표
  ```

### Phase 2: API 엔드포인트 구현
- [ ] `/api/stock/<symbol>` - 종목 전체 데이터
  - Quote, TTM Ratios, Key Metrics
  - Annual/Quarterly 재무제표 (3년/8분기)
  - 차트용 데이터 (ROE, 매출, 성장률)
- [ ] `/api/macro` - 거시경제 지표
  - VIX, 10Y, FCI, HY Spread, Dollar Index, Margin Debt
- [ ] `/api/stock/<symbol>/technicals` - 기술적 지표
  - RSI, 이평선 이격도

### Phase 3: 캐싱 및 최적화
- [ ] Redis 또는 메모리 캐시 구현
- [ ] API 응답 캐싱 (5분 TTL)
- [ ] 에러 핸들링 및 로깅
- [ ] Rate limiting (API 호출 제한)

### Phase 4: Frontend 연동
- [ ] `dashboard_v3_ui.html` 수정
  - Fetch API로 서버 호출
  - 로딩 상태 표시
  - 에러 처리
- [ ] Chart.js 통합
  ```javascript
  // ROE 추이 차트
  // 매출 vs 순이익 차트
  // EPS 성장률 차트
  ```

### Phase 5: 차트 구현
- [ ] Chart.js 라이브러리 추가
- [ ] ROE 추이 차트 (막대 그래프)
- [ ] 매출 vs 순이익 차트 (이중 축 선 그래프)
- [ ] EPS & 성장률 차트 (막대 + 선 복합)
- [ ] 자기자본 & 부채비율 추이

### Phase 6: 배포
- [ ] 서버 환경 설정 (Python 3.9+, pip)
- [ ] 환경변수 설정 (API 키)
- [ ] `requirements.txt` 생성
- [ ] 서버 실행 및 테스트
- [ ] 프론트엔드 배포 (GitHub Pages 또는 동일 서버)

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
# ~/.zshrc 또는 .env
export FMP_API_KEY="your_fmp_api_key"
export FRED_API_KEY="your_fred_api_key"
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
```

### 3. Flask 서버 실행 (작업 예정)
```bash
cd scripts
python flask_server.py
# 서버: http://localhost:5000
```

### 4. 프론트엔드 접근
```
브라우저에서: http://localhost:5000
또는 data/dashboard_v3_ui.html 직접 열기 (개발용)
```

## API 응답 예시

### GET /api/stock/NVDA
```json
{
  "symbol": "NVDA",
  "generated_at": "2026-07-17T14:30:00",
  "quote": {
    "price": 207.4,
    "change": 8.18,
    "changesPercentage": 4.03,
    "marketCap": 5110000000000,
    "priceAvg50": 209.24,
    "priceAvg200": 191.53
  },
  "financials": {
    "ttm": {
      "pegRatio": 0.3,
      "peRatio": 32.1,
      "roe": 0.8165
    },
    "annual": {
      "income": [...],
      "balance": [...],
      "growth": [...]
    }
  },
  "charts": {
    "roe_annual": [
      {"date": "2026-01-25", "roe": 76.33, "netIncome": 120067000000, "equity": 157293000000},
      ...
    ]
  }
}
```

## 데이터 수집 주기

- **실시간**: 종목 검색 시 API 호출
- **캐싱**: 5분간 동일 종목 재조회 시 캐시 반환
- **거시경제**: 매일 1회 업데이트 (FRED 데이터는 일별)

## 주요 분석 지표

### 재무 지표
- **ROE (Return on Equity)**: 자기자본이익률
- **PEG Ratio**: 주가수익성장비율 (P/E ÷ EPS Growth)
- **P/E Ratio**: 주가수익비율
- **EPS Growth**: 주당순이익 성장률
- **Revenue Growth**: 매출 성장률

### 기술적 지표
- **RSI(14)**: 상대강도지수
- **50일/200일 이평선 이격도**: 현재가 대비 이격률

### 거시경제 지표
- **VIX**: 변동성 지수
- **10Y Treasury**: 10년물 국채 금리
- **FCI**: 금융상황지수
- **HY Spread**: 하이일드 스프레드
- **Dollar Index**: 달러 인덱스
- **Margin Debt**: 마진 부채
- **Above MA(200)**: 200일 이평선 상회 비율

## 개발 노트

### FMP API 엔드포인트 수정 사항
- `/stable` 베이스 URL 사용
- 쿼리 파라미터로 `symbol=` 전달 (경로 파라미터 아님)
- 올바른 URL 형식:
  ```
  ✅ /stable/income-statement?symbol=NVDA&period=annual
  ❌ /stable/income-statement/NVDA?period=annual
  ```

### 차트 데이터 구조
- 모든 차트 데이터는 `charts` 객체에 저장
- 날짜 내림차순 정렬 (최신 데이터가 먼저)
- 금액은 달러 단위, 비율은 소수점 (0.6599 = 65.99%)

## 라이센스

MIT License

## 작성자

hoonick

## 버전

- v0.3 (2026-07-17) - Flask 서버 구조 설계, UI 프로토타입 완성
- v0.2 (2026-07-11) - 재무제표 수집 기능 추가, 대시보드 v2
- v0.1 (2026-07-10) - 초기 프로젝트 설정, API 클라이언트 구축
