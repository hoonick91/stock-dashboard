"""
Alpha Vantage API 데이터 수집기
주가, 기술지표, 재무비율 수집
"""

import requests
import pandas as pd
from datetime import datetime
import os
import time


class AlphaVantageClient:
    """Alpha Vantage API 클라이언트"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key=None):
        """
        Args:
            api_key: Alpha Vantage API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY가 설정되지 않았습니다.")

    def get_quote(self, symbol):
        """
        실시간 시세 조회

        Args:
            symbol: 티커 심볼 (예: AAPL, MSFT)

        Returns:
            dict: 시세 정보
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "Global Quote" not in data:
                print(f"시세 조회 실패 ({symbol}): {data}")
                return None

            quote = data["Global Quote"]

            return {
                "symbol": quote.get("01. symbol"),
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "changesPercentage": float(quote.get("10. change percent", "0").replace("%", "")),
                "volume": int(quote.get("06. volume", 0)),
            }

        except Exception as e:
            print(f"시세 조회 실패 ({symbol}): {e}")
            return None

    def get_rsi(self, symbol, interval="daily", time_period=14):
        """
        RSI 조회

        Args:
            symbol: 티커 심볼
            interval: daily, weekly, monthly
            time_period: RSI 기간 (보통 14)

        Returns:
            pandas.DataFrame: RSI 데이터
        """
        params = {
            "function": "RSI",
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": "close",
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "Technical Analysis: RSI" not in data:
                print(f"RSI 조회 실패 ({symbol}): {data}")
                return None

            rsi_data = data["Technical Analysis: RSI"]

            # DataFrame 변환
            df = pd.DataFrame.from_dict(rsi_data, orient='index')
            df.index = pd.to_datetime(df.index)
            df.columns = ['rsi']
            df['rsi'] = df['rsi'].astype(float)
            df = df.sort_index()

            return df.reset_index().rename(columns={'index': 'date'})

        except Exception as e:
            print(f"RSI 조회 실패 ({symbol}): {e}")
            return None

    def get_sma(self, symbol, interval="daily", time_period=50):
        """
        단순 이동평균 조회

        Args:
            symbol: 티커 심볼
            interval: daily, weekly, monthly
            time_period: 이동평균 기간

        Returns:
            pandas.DataFrame: SMA 데이터
        """
        params = {
            "function": "SMA",
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": "close",
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "Technical Analysis: SMA" not in data:
                print(f"SMA 조회 실패 ({symbol}): {data}")
                return None

            sma_data = data["Technical Analysis: SMA"]

            # DataFrame 변환
            df = pd.DataFrame.from_dict(sma_data, orient='index')
            df.index = pd.to_datetime(df.index)
            df.columns = [f'sma_{time_period}']
            df[f'sma_{time_period}'] = df[f'sma_{time_period}'].astype(float)
            df = df.sort_index()

            return df.reset_index().rename(columns={'index': 'date'})

        except Exception as e:
            print(f"SMA 조회 실패 ({symbol}): {e}")
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
        try:
            # 현재가
            quote = self.get_quote(symbol)
            if not quote:
                return None

            current_price = quote["price"]

            # API 제한 (5 calls/minute for free tier)
            time.sleep(15)

            # 이동평균
            sma_data = self.get_sma(symbol, time_period=sma_period)
            if sma_data is None or len(sma_data) == 0:
                return None

            sma_value = sma_data.iloc[-1][f'sma_{sma_period}']

            # 이격도 계산
            divergence = (current_price / sma_value) * 100

            return {
                "symbol": symbol,
                "current_price": current_price,
                f"sma_{sma_period}": sma_value,
                "divergence": round(divergence, 2),
                "date": datetime.now().strftime("%Y-%m-%d")
            }

        except Exception as e:
            print(f"이격도 계산 실패 ({symbol}): {e}")
            return None


def analyze_stock(symbol):
    """
    종목 종합 분석

    Args:
        symbol: 티커 심볼

    Returns:
        dict: 종합 분석 결과
    """
    client = AlphaVantageClient()

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

    # API 제한 대응
    time.sleep(15)

    # 2. RSI
    print("2. RSI 조회 중...")
    rsi_data = client.get_rsi(symbol, time_period=14)
    if rsi_data is not None and len(rsi_data) > 0:
        rsi_value = rsi_data.iloc[-1]["rsi"]
        result["rsi"] = rsi_value
        print(f"   RSI(14): {rsi_value:.2f}")

    # API 제한 대응
    time.sleep(15)

    # 3. 50일 이동평균 & 이격도
    print("3. 50일 이동평균 조회 중...")
    div = client.calculate_divergence(symbol, 50)
    if div:
        result["sma_50"] = div["sma_50"]
        result["divergence_50"] = div["divergence"]
        print(f"   50일 이평: ${div['sma_50']:.2f} (이격도: {div['divergence']:.2f}%)")

    return result


if __name__ == "__main__":
    print("=" * 50)
    print("Alpha Vantage 데이터 수집 시작")
    print("=" * 50)
    print("주의: 무료 플랜은 5 calls/minute 제한이 있습니다.")
    print("=" * 50)

    # 테스트: 1개 종목만 (API 제한 때문에)
    test_symbol = "AAPL"

    result = analyze_stock(test_symbol)

    print("\n" + "=" * 50)
    print("분석 결과")
    print("=" * 50)
    for key, value in result.items():
        print(f"{key}: {value}")

    # CSV 저장
    output_dir = "../data"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/stock_analysis_{test_symbol}_{timestamp}.csv"

    df = pd.DataFrame([result])
    df.to_csv(filename, index=False)
    print(f"\n✓ 저장 완료: {filename}")
