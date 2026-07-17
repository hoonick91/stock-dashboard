"""
일일 투자 모니터링 스크립트
거시경제 지표 + 개별 종목 분석
"""

import os
import pandas as pd
from datetime import datetime
import time
from fred_api import FREDClient
from fmp_api import FMPClient
from alphavantage_api import AlphaVantageClient


class DailyMonitor:
    """일일 모니터링 클래스"""

    def __init__(self):
        self.fred = FREDClient()
        self.fmp = FMPClient()
        self.alpha = AlphaVantageClient()
        self.report_data = {}

    def collect_macro_indicators(self):
        """거시경제 지표 수집"""
        print("\n" + "=" * 60)
        print("거시경제 지표 수집 중...")
        print("=" * 60)

        indicators = {
            "VIX": "VIXCLS",
            "10Y_Treasury": "DGS10",
            "FCI": "NFCI",
            "HY_Spread": "BAMLH0A0HYM2",
            "Dollar_Index": "DTWEXBGS",
            "Margin_Debt": "BOGZ1FL663067003Q"
        }

        macro_data = {}

        for name, series_id in indicators.items():
            data = self.fred.get_latest_value(series_id)
            if data:
                macro_data[name] = {
                    "value": data["value"],
                    "date": data["date"]
                }
                print(f"✓ {name}: {data['value']:.2f} ({data['date']})")
            else:
                macro_data[name] = {"value": None, "date": None}
                print(f"✗ {name}: 데이터 없음")

        # 이평선 상회 비중 (대형주 샘플 기준)
        print("\n이평선 상회 비중 계산 중... (대형주 10개 샘플)")
        above_ma_ratio = self.calculate_above_ma_ratio()
        if above_ma_ratio is not None:
            macro_data["Above_MA_Ratio"] = {
                "value": above_ma_ratio,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            print(f"✓ Above MA(200) Ratio: {above_ma_ratio:.1f}% (샘플)")
        else:
            macro_data["Above_MA_Ratio"] = {"value": None, "date": None}
            print(f"✗ Above MA Ratio: 계산 실패")

        self.report_data["macro"] = macro_data
        return macro_data

    def calculate_above_ma_ratio(self):
        """
        이평선(200일) 상회 비중 계산
        대형주 샘플로 근사치 계산 (API 제한 고려)
        """
        # 대표 대형주 샘플 (시총 상위 10개 정도)
        sample_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
            "META", "TSLA", "BRK.B", "UNH", "XOM"
        ]

        above_count = 0
        total_count = 0

        for symbol in sample_stocks:
            try:
                quote = self.fmp.get_quote(symbol)
                if quote and quote.get("priceAvg200"):
                    price = quote["price"]
                    ma200 = quote["priceAvg200"]

                    if price > ma200:
                        above_count += 1
                    total_count += 1

                    # API 제한 고려 (간략한 딜레이)
                    time.sleep(0.5)
            except Exception as e:
                print(f"  ✗ {symbol} 조회 실패: {e}")
                continue

        if total_count > 0:
            ratio = (above_count / total_count) * 100
            return round(ratio, 1)
        return None

    def collect_stock_data(self, symbol):
        """개별 종목 데이터 수집"""
        print("\n" + "=" * 60)
        print(f"{symbol} 종목 데이터 수집 중...")
        print("=" * 60)

        stock_data = {"symbol": symbol}

        # 1. 시세 정보
        print(f"\n[1/4] 시세 조회...")
        quote = self.fmp.get_quote(symbol)
        if quote:
            stock_data["price"] = quote["price"]
            stock_data["change_percent"] = quote.get("changePercentage", 0)
            stock_data["sma_50"] = quote.get("priceAvg50")
            stock_data["sma_200"] = quote.get("priceAvg200")

            # 이격도 계산
            if stock_data["sma_50"]:
                stock_data["divergence_50"] = round((quote["price"] / stock_data["sma_50"]) * 100, 2)
            if stock_data["sma_200"]:
                stock_data["divergence_200"] = round((quote["price"] / stock_data["sma_200"]) * 100, 2)

            print(f"✓ 현재가: ${quote['price']:.2f} ({quote.get('changePercentage', 0):+.2f}%)")
            print(f"✓ 50일 이평: ${stock_data.get('sma_50', 0):.2f} (이격도: {stock_data.get('divergence_50', 0):.2f}%)")
            print(f"✓ 200일 이평: ${stock_data.get('sma_200', 0):.2f} (이격도: {stock_data.get('divergence_200', 0):.2f}%)")
        else:
            print(f"✗ 시세 조회 실패")

        # API 제한 대응 (15초 대기)
        print("\n[2/4] RSI 조회 중... (15초 대기)")
        time.sleep(15)

        # 2. RSI
        rsi_data = self.alpha.get_rsi(symbol, time_period=14)
        if rsi_data is not None and len(rsi_data) > 0:
            rsi_value = rsi_data.iloc[-1]["rsi"]
            stock_data["rsi"] = rsi_value

            # RSI 해석
            if rsi_value >= 70:
                rsi_status = "과매수"
            elif rsi_value <= 30:
                rsi_status = "과매도"
            else:
                rsi_status = "중립"

            stock_data["rsi_status"] = rsi_status
            print(f"✓ RSI(14): {rsi_value:.2f} ({rsi_status})")
        else:
            print(f"✗ RSI 조회 실패")

        # 3. 재무지표
        print("\n[3/4] 재무지표 조회 중...")
        metrics = self.fmp.get_key_metrics(symbol)
        if metrics:
            stock_data["roe"] = metrics.get("returnOnEquityTTM")
            stock_data["market_cap"] = metrics.get("marketCap")

            # P/E 계산
            earnings_yield = metrics.get("earningsYieldTTM")
            if earnings_yield and earnings_yield > 0:
                stock_data["per"] = round(1 / earnings_yield, 2)

            print(f"✓ ROE: {stock_data.get('roe', 0):.4f}")
            print(f"✓ P/E: {stock_data.get('per', 'N/A')}")
            print(f"✓ Market Cap: ${stock_data.get('market_cap', 0):,.0f}")
        else:
            print(f"✗ 재무지표 조회 실패")

        # PEG Ratio (ratios-ttm endpoint)
        ratios = self.fmp.get_ratios(symbol, period="ttm", limit=1)
        if ratios is not None and len(ratios) > 0:
            peg = ratios.iloc[0].get("priceToEarningsGrowthRatioTTM")
            if peg:
                stock_data["peg"] = round(peg, 2)
                print(f"✓ PEG: {stock_data.get('peg', 'N/A')}")
        else:
            print(f"✗ PEG Ratio 조회 실패")

        # 4. 회사 정보
        print("\n[4/4] 회사 정보 조회 중...")
        profile = self.fmp.get_quote(symbol)  # quote에 회사명 포함
        if profile:
            stock_data["company_name"] = profile.get("name", symbol)
            print(f"✓ 회사명: {stock_data['company_name']}")

        self.report_data["stock"] = stock_data
        return stock_data

    def generate_report(self):
        """리포트 생성"""
        print("\n" + "=" * 60)
        print("📊 일일 투자 모니터링 리포트")
        print("=" * 60)
        print(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 거시경제 환경
        macro = self.report_data.get("macro", {})
        print("\n[거시경제 환경]")

        vix = macro.get("VIX", {}).get("value")
        if vix:
            vix_status = "안정" if vix < 20 else ("경계" if vix < 30 else "공포")
            print(f"VIX: {vix:.2f} ({vix_status})")

        treasury = macro.get("10Y_Treasury", {}).get("value")
        if treasury:
            print(f"10년물 금리: {treasury:.2f}%")

        hy = macro.get("HY_Spread", {}).get("value")
        if hy:
            hy_status = "양호" if hy < 5 else ("경계" if hy < 7 else "위험")
            print(f"하이일드 스프레드: {hy:.2f}% ({hy_status})")

        fci = macro.get("FCI", {}).get("value")
        if fci:
            fci_status = "완화" if fci < 0 else "긴축"
            print(f"금융상황지수: {fci:.2f} ({fci_status})")

        dollar = macro.get("Dollar_Index", {}).get("value")
        if dollar:
            print(f"달러 인덱스: {dollar:.2f}")

        margin = macro.get("Margin_Debt", {}).get("value")
        if margin:
            print(f"마진 부채: ${margin:,.0f}B (분기별)")

        above_ma = macro.get("Above_MA_Ratio", {}).get("value")
        if above_ma is not None:
            ma_status = "강세" if above_ma >= 70 else ("약세" if above_ma <= 30 else "중립")
            print(f"이평선(200일) 상회 비중: {above_ma:.1f}% ({ma_status}, 대형주 샘플)")

        # 종목 분석
        stock = self.report_data.get("stock", {})
        if stock:
            print(f"\n[{stock.get('symbol', 'N/A')} 분석]")
            print(f"회사명: {stock.get('company_name', 'N/A')}")

            price = stock.get("price")
            change = stock.get("change_percent")
            if price:
                print(f"현재가: ${price:.2f} ({change:+.2f}%)")

            sma50 = stock.get("sma_50")
            div50 = stock.get("divergence_50")
            if sma50:
                print(f"50일 이평: ${sma50:.2f} (이격도: {div50:.2f}%)")

            sma200 = stock.get("sma_200")
            div200 = stock.get("divergence_200")
            if sma200:
                print(f"200일 이평: ${sma200:.2f} (이격도: {div200:.2f}%)")

            rsi = stock.get("rsi")
            rsi_status = stock.get("rsi_status")
            if rsi:
                print(f"RSI(14): {rsi:.2f} ({rsi_status})")

            per = stock.get("per")
            if per:
                print(f"P/E Ratio: {per:.2f}")

            peg = stock.get("peg")
            if peg:
                print(f"PEG Ratio: {peg:.2f}")

            roe = stock.get("roe")
            if roe:
                print(f"ROE: {roe * 100:.2f}%")

            mcap = stock.get("market_cap")
            if mcap:
                print(f"시가총액: ${mcap:,.0f}")

        print("\n" + "=" * 60)

    def save_to_csv(self, symbol):
        """CSV로 저장"""
        output_dir = "../data"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{output_dir}/daily_report_{symbol}_{timestamp}.csv"

        # 데이터 평탄화
        data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
        }

        # 거시경제
        macro = self.report_data.get("macro", {})
        for key, val in macro.items():
            if isinstance(val, dict):
                data[key] = val.get("value")

        # 종목
        stock = self.report_data.get("stock", {})
        for key, val in stock.items():
            if key != "symbol":
                data[key] = val

        # DataFrame 생성 및 저장
        df = pd.DataFrame([data])
        df.to_csv(filename, index=False)

        print(f"\n✓ 리포트 저장: {filename}")
        return filename


def main(symbol="CRCL"):
    """메인 실행"""
    monitor = DailyMonitor()

    # 1. 거시경제 지표 수집
    monitor.collect_macro_indicators()

    # 2. 종목 데이터 수집
    monitor.collect_stock_data(symbol)

    # 3. 리포트 생성
    monitor.generate_report()

    # 4. CSV 저장
    monitor.save_to_csv(symbol)

    print("\n✅ 일일 모니터링 완료!")


if __name__ == "__main__":
    import sys

    # 명령행 인수로 종목 지정 가능
    symbol = sys.argv[1] if len(sys.argv) > 1 else "CRCL"

    print(f"\n{'=' * 60}")
    print(f"일일 투자 모니터링 시작: {symbol}")
    print(f"{'=' * 60}")

    main(symbol)
