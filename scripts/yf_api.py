"""
Yahoo Finance API 데이터 수집기 (yfinance)
주가, 기술지표, 재무비율 수집 - 완전 무료, API 키 불필요
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os


class YFClient:
    """Yahoo Finance 클라이언트"""

    def get_quote(self, symbol):
        """
        실시간 시세 조회

        Args:
            symbol: 티커 심볼 (예: AAPL, MSFT)

        Returns:
            dict: 시세 정보
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "price": info.get("currentPrice", info.get("regularMarketPrice")),
                "change": info.get("regularMarketChange"),
                "changesPercentage": info.get("regularMarketChangePercent"),
                "dayHigh": info.get("dayHigh"),
                "dayLow": info.get("dayLow"),
                "volume": info.get("volume"),
            }
        except Exception as e:
            print(f"시세 조회 실패 ({symbol}): {e}")
            return None

    def get_historical_data(self, symbol, period="1mo", interval="1d"):
        """
        과거 주가 데이터 조회

        Args:
            symbol: 티커 심볼
            period: 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 간격 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            pandas.DataFrame: OHLCV 데이터
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            return df
        except Exception as e:
            print(f"과거 데이터 조회 실패 ({symbol}): {e}")
            return None

    def calculate_sma(self, symbol, period=50, days=30):
        """
        단순 이동평균 계산

        Args:
            symbol: 티커 심볼
            period: 이동평균 기간 (일)
            days: 조회할 데이터 일수

        Returns:
            pandas.DataFrame: 날짜별 종가 및 SMA
        """
        try:
            # period + days 만큼 데이터 가져오기 (SMA 계산 위해)
            total_days = period + days
            df = self.get_historical_data(symbol, period=f"{total_days}d")

            if df is None or len(df) == 0:
                return None

            # SMA 계산
            df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()

            # 최근 days개만 반환
            result = df[['Close', f'SMA_{period}']].tail(days).copy()
            result = result.reset_index()
            result.columns = ['date', 'close', f'sma_{period}']

            return result

        except Exception as e:
            print(f"SMA 계산 실패 ({symbol}): {e}")
            return None

    def calculate_rsi(self, symbol, period=14, days=30):
        """
        RSI (Relative Strength Index) 계산

        Args:
            symbol: 티커 심볼
            period: RSI 기간 (보통 14)
            days: 조회할 데이터 일수

        Returns:
            pandas.DataFrame: 날짜별 RSI
        """
        try:
            total_days = period + days + 10
            df = self.get_historical_data(symbol, period=f"{total_days}d")

            if df is None or len(df) == 0:
                return None

            # 가격 변화
            delta = df['Close'].diff()

            # 상승/하락 분리
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            # RS 및 RSI 계산
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            df['RSI'] = rsi

            # 최근 days개만 반환
            result = df[['Close', 'RSI']].tail(days).copy()
            result = result.reset_index()
            result.columns = ['date', 'close', 'rsi']

            return result

        except Exception as e:
            print(f"RSI 계산 실패 ({symbol}): {e}")
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

            # 이동평균 (최근 1개만)
            sma_data = self.calculate_sma(symbol, sma_period, days=1)
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

    def get_financials(self, symbol):
        """
        재무 지표 조회 (PER, PBR 등)

        Args:
            symbol: 티커 심볼

        Returns:
            dict: 재무 비율
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "pb_ratio": info.get("priceToBook"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "market_cap": info.get("marketCap"),
                "eps": info.get("trailingEps"),
                "roe": info.get("returnOnEquity"),
            }

        except Exception as e:
            print(f"재무지표 조회 실패 ({symbol}): {e}")
            return None


def analyze_stock(symbol):
    """
    종목 종합 분석

    Args:
        symbol: 티커 심볼

    Returns:
        dict: 종합 분석 결과
    """
    client = YFClient()

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
    rsi_data = client.calculate_rsi(symbol, 14, days=1)
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

    # 4. 재무 지표
    print("4. 재무지표 조회 중...")
    financials = client.get_financials(symbol)
    if financials:
        if financials.get("pe_ratio"):
            result["per"] = financials["pe_ratio"]
            print(f"   PER: {financials['pe_ratio']:.2f}")
        if financials.get("peg_ratio"):
            result["peg"] = financials["peg_ratio"]
            print(f"   PEG: {financials['peg_ratio']:.2f}")

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
    print("Yahoo Finance 데이터 수집 시작")
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
