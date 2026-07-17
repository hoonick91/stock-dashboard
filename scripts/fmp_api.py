"""
Financial Modeling Prep API 데이터 수집기
주가, 기술지표, 재무비율 수집
"""

import requests
import pandas as pd
from datetime import datetime
import os


class FMPClient:
    """Financial Modeling Prep API 클라이언트"""

    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key=None):
        """
        Args:
            api_key: FMP API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError("FMP_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    def get_quote(self, symbol):
        """
        실시간 시세 조회

        Args:
            symbol: 티커 심볼 (예: AAPL, MSFT)

        Returns:
            dict: 시세 정보
        """
        url = f"{self.BASE_URL}/quote"
        params = {"symbol": symbol, "apikey": self.api_key}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data[0] if data else None
        except Exception as e:
            print(f"시세 조회 실패 ({symbol}): {e}")
            return None

    def get_technical_indicator(self, symbol, indicator_type="rsi", period=14, limit=30):
        """
        기술지표 조회

        Args:
            symbol: 티커 심볼
            indicator_type: 지표 타입 (rsi, sma, ema, wma)
            period: 기간 (5, 20, 50, 200 등)
            limit: 데이터 포인트 개수

        Returns:
            pandas.DataFrame: 기술지표 데이터
        """
        url = f"{self.BASE_URL}/technical_indicator/daily/{symbol}"
        params = {
            "type": indicator_type,
            "period": period,
            "apikey": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            # 최근 limit개만
            df = pd.DataFrame(data[:limit])
            df["date"] = pd.to_datetime(df["date"])

            # 날짜 내림차순 → 오름차순
            df = df.sort_values("date").reset_index(drop=True)

            return df

        except Exception as e:
            print(f"기술지표 조회 실패 ({symbol} - {indicator_type}): {e}")
            return None

    def get_key_metrics(self, symbol):
        """
        주요 재무 지표 조회 (PER, PEG 등) - TTM

        Args:
            symbol: 티커 심볼

        Returns:
            dict: 재무 지표
        """
        url = f"{self.BASE_URL}/key-metrics-ttm"
        params = {
            "symbol": symbol,
            "apikey": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            return data[0] if isinstance(data, list) else data

        except Exception as e:
            print(f"재무지표 조회 실패 ({symbol}): {e}")
            return None

    def get_ratios(self, symbol, period="annual", limit=5):
        """
        재무 비율 조회 (PER, PBR, ROE 등)

        Args:
            symbol: 티커 심볼
            period: annual, quarter, 또는 ttm
            limit: 데이터 개수

        Returns:
            pandas.DataFrame: 재무 비율
        """
        # TTM은 별도 엔드포인트 사용
        if period.lower() == "ttm":
            url = f"{self.BASE_URL}/ratios-ttm"
            params = {
                "symbol": symbol,
                "apikey": self.api_key
            }
        else:
            url = f"{self.BASE_URL}/ratios/{symbol}"
            params = {
                "period": period,
                "limit": limit,
                "apikey": self.api_key
            }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            df = pd.DataFrame(data if isinstance(data, list) else [data])
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])

            return df

        except Exception as e:
            print(f"재무비율 조회 실패 ({symbol}): {e}")
            return None

    def get_income_statement(self, symbol, period="annual", limit=5):
        """
        손익계산서 조회

        Args:
            symbol: 티커 심볼
            period: annual 또는 quarter
            limit: 데이터 개수

        Returns:
            list: 손익계산서 데이터
        """
        url = f"{self.BASE_URL}/income-statement"
        params = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "apikey": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data if data else None

        except Exception as e:
            print(f"손익계산서 조회 실패 ({symbol}): {e}")
            return None

    def get_balance_sheet(self, symbol, period="annual", limit=5):
        """
        대차대조표 조회

        Args:
            symbol: 티커 심볼
            period: annual 또는 quarter
            limit: 데이터 개수

        Returns:
            list: 대차대조표 데이터
        """
        url = f"{self.BASE_URL}/balance-sheet-statement"
        params = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "apikey": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data if data else None

        except Exception as e:
            print(f"대차대조표 조회 실패 ({symbol}): {e}")
            return None

    def get_financial_growth(self, symbol, period="annual", limit=5):
        """
        재무 성장률 조회

        Args:
            symbol: 티커 심볼
            period: annual 또는 quarter
            limit: 데이터 개수

        Returns:
            list: 성장률 데이터
        """
        url = f"{self.BASE_URL}/financial-growth"
        params = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "apikey": self.api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data if data else None

        except Exception as e:
            print(f"성장률 조회 실패 ({symbol}): {e}")
            return None

    def calculate_divergence(self, symbol, sma_period=50):
        """
        이격도 계산 (현재가 / 이동평균 × 100)

        Args:
            symbol: 티커 심볼
            sma_period: 이동평균 기간

        Returns:
            dict: {"current_price": 180.5, "sma": 175.2, "divergence": 103.0}
        """
        # 현재가
        quote = self.get_quote(symbol)
        if not quote:
            return None

        current_price = quote["price"]

        # 이동평균
        sma_data = self.get_technical_indicator(symbol, "sma", sma_period, limit=1)
        if sma_data is None or len(sma_data) == 0:
            return None

        sma_value = sma_data.iloc[-1]["sma"]

        # 이격도 계산
        divergence = (current_price / sma_value) * 100

        return {
            "symbol": symbol,
            "current_price": current_price,
            f"sma_{sma_period}": sma_value,
            "divergence": round(divergence, 2),
            "date": datetime.now().strftime("%Y-%m-%d")
        }


def analyze_stock(symbol):
    """
    종목 종합 분석

    Args:
        symbol: 티커 심볼

    Returns:
        dict: 종합 분석 결과
    """
    client = FMPClient()

    print(f"\n{'=' * 50}")
    print(f"종목 분석: {symbol}")
    print(f"{'=' * 50}")

    result = {"symbol": symbol}

    # 1. 현재 시세
    print("1. 시세 조회 중...")
    quote = client.get_quote(symbol)
    if quote:
        result["price"] = quote["price"]
        result["change_percent"] = quote["changesPercentage"]
        print(f"   현재가: ${quote['price']:.2f} ({quote['changesPercentage']:+.2f}%)")

    # 2. RSI
    print("2. RSI 조회 중...")
    rsi_data = client.get_technical_indicator(symbol, "rsi", 14, limit=1)
    if rsi_data is not None and len(rsi_data) > 0:
        rsi_value = rsi_data.iloc[-1]["rsi"]
        result["rsi"] = rsi_value
        print(f"   RSI(14): {rsi_value:.2f}")

    # 3. 50일/200일 이동평균 & 이격도
    print("3. 이동평균 조회 중...")
    for period in [50, 200]:
        div = client.calculate_divergence(symbol, period)
        if div:
            result[f"sma_{period}"] = div[f"sma_{period}"]
            result[f"divergence_{period}"] = div["divergence"]
            print(f"   {period}일 이평: ${div[f'sma_{period}']:.2f} (이격도: {div['divergence']:.2f}%)")

    # 4. 재무 지표 (PER, PEG)
    print("4. 재무지표 조회 중...")
    metrics = client.get_key_metrics(symbol, limit=1)
    if metrics is not None and len(metrics) > 0:
        latest = metrics.iloc[0]
        if "peRatio" in latest:
            result["per"] = latest["peRatio"]
            print(f"   PER: {latest['peRatio']:.2f}")
        if "pegRatio" in latest:
            result["peg"] = latest["pegRatio"]
            print(f"   PEG: {latest['pegRatio']:.2f}")

    return result


def analyze_portfolio(symbols):
    """
    포트폴리오 일괄 분석

    Args:
        symbols: 티커 심볼 리스트

    Returns:
        pandas.DataFrame: 분석 결과
    """
    results = []

    for symbol in symbols:
        try:
            result = analyze_stock(symbol)
            results.append(result)
        except Exception as e:
            print(f"✗ {symbol} 분석 실패: {e}")

    if results:
        df = pd.DataFrame(results)
        return df
    return None


if __name__ == "__main__":
    print("=" * 50)
    print("FMP API 데이터 수집 시작")
    print("=" * 50)

    # 테스트: 대표 종목 분석
    test_symbols = ["AAPL", "MSFT", "NVDA"]

    df = analyze_portfolio(test_symbols)

    if df is not None:
        print("\n" + "=" * 50)
        print("분석 결과 요약")
        print("=" * 50)
        print(df.to_string(index=False))

        # CSV 저장
        output_dir = "../data"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/portfolio_analysis_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"\n✓ 저장 완료: {filename}")
    else:
        print("\n✗ 분석 실패")
