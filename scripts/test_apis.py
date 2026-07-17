"""
API 테스트 스크립트
FRED와 FMP API가 정상 작동하는지 확인
"""

import sys
from fred_api import FREDClient, get_all_indicators
from fmp_api import FMPClient, analyze_stock

def test_fred():
    """FRED API 테스트"""
    print("=" * 60)
    print("FRED API 테스트")
    print("=" * 60)

    try:
        client = FREDClient()

        # VIX 테스트
        print("\n[테스트 1] VIX 조회")
        vix = client.get_latest_value("VIXCLS")
        if vix:
            print(f"✓ VIX: {vix['value']:.2f} ({vix['date']})")
        else:
            print("✗ VIX 조회 실패")
            return False

        # 10년물 금리 테스트
        print("\n[테스트 2] 10년물 금리 조회")
        treasury = client.get_latest_value("DGS10")
        if treasury:
            print(f"✓ 10년물: {treasury['value']:.2f}% ({treasury['date']})")
        else:
            print("✗ 10년물 조회 실패")
            return False

        # 하이일드 스프레드
        print("\n[테스트 3] 하이일드 스프레드 조회")
        hy = client.get_latest_value("BAMLH0A0HYM2")
        if hy:
            print(f"✓ HY Spread: {hy['value']:.2f}% ({hy['date']})")
        else:
            print("✗ HY Spread 조회 실패")
            return False

        print("\n✓ FRED API 테스트 성공!")
        return True

    except Exception as e:
        print(f"\n✗ FRED API 테스트 실패: {e}")
        return False


def test_fmp():
    """FMP API 테스트"""
    print("\n" + "=" * 60)
    print("FMP API 테스트")
    print("=" * 60)

    try:
        client = FMPClient()

        # 시세 조회
        print("\n[테스트 1] AAPL 시세 조회")
        quote = client.get_quote("AAPL")
        if quote:
            print(f"✓ 현재가: ${quote['price']:.2f} ({quote.get('changePercentage', 0):+.2f}%)")
        else:
            print("✗ 시세 조회 실패")
            return False

        # 재무지표 (TTM)
        print("\n[테스트 2] 재무지표 조회")
        metrics = client.get_key_metrics("AAPL")
        if metrics:
            print(f"✓ ROE: {metrics.get('returnOnEquityTTM', 'N/A')}")
            print(f"✓ Market Cap: ${metrics.get('marketCap', 0):,.0f}")
            print(f"✓ P/E (Earnings Yield의 역수): {1/metrics.get('earningsYieldTTM', 1):.2f}")
        else:
            print("✗ 재무지표 조회 실패")
            return False

        print("\n✓ FMP API 테스트 성공!")
        return True

    except Exception as e:
        print(f"\n✗ FMP API 테스트 실패: {e}")
        return False


def main():
    """전체 테스트 실행"""
    print("\n" + "=" * 60)
    print("API 테스트 시작")
    print("=" * 60)

    # FRED 테스트
    fred_ok = test_fred()

    # FMP 테스트
    fmp_ok = test_fmp()

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"FRED API: {'✓ 성공' if fred_ok else '✗ 실패'}")
    print(f"FMP API:  {'✓ 성공' if fmp_ok else '✗ 실패'}")

    if fred_ok and fmp_ok:
        print("\n🎉 모든 테스트 통과! API 설정이 완료되었습니다.")
        return 0
    else:
        print("\n⚠️  일부 테스트 실패. 환경변수를 확인하세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
