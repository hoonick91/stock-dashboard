"""
FRED API 데이터 수집기
미국 연방준비은행(Federal Reserve Economic Data) API로 거시경제 지표 수집
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os

class FREDClient:
    """FRED API 클라이언트"""

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key=None):
        """
        Args:
            api_key: FRED API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            raise ValueError("FRED_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    def get_series(self, series_id, start_date=None, end_date=None):
        """
        FRED 시계열 데이터 조회

        Args:
            series_id: FRED 시리즈 코드 (예: DGS10, VIXCLS)
            start_date: 시작일 (YYYY-MM-DD) - 기본값: 30일 전
            end_date: 종료일 (YYYY-MM-DD) - 기본값: 오늘

        Returns:
            pandas.DataFrame: date, value 컬럼을 가진 데이터프레임
        """
        # 기본 날짜 설정
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            # 데이터프레임 변환
            df = pd.DataFrame(data["observations"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"])

            # NaN 제거 (주말/휴일 등)
            df = df.dropna(subset=["value"])

            return df[["date", "value"]]

        except requests.exceptions.RequestException as e:
            print(f"API 요청 실패: {e}")
            return None
        except Exception as e:
            print(f"데이터 처리 실패: {e}")
            return None

    def get_latest_value(self, series_id):
        """
        최신 값만 조회

        Args:
            series_id: FRED 시리즈 코드

        Returns:
            dict: {"date": "2026-06-27", "value": 15.2}
        """
        # 먼저 30일 시도
        df = self.get_series(series_id)

        # 데이터 없으면 1년으로 확장 (분기/월간 데이터 대응)
        if df is None or len(df) == 0:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            df = self.get_series(series_id, start_date, end_date)

        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            return {
                "date": latest["date"].strftime("%Y-%m-%d"),
                "value": latest["value"]
            }
        return None


def get_all_indicators(days=30):
    """
    모든 주요 지표 한 번에 조회

    Args:
        days: 과거 며칠 데이터 (기본 30일)

    Returns:
        dict: 지표명을 키로 하는 딕셔너리
    """
    client = FREDClient()

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    indicators = {
        "VIX": "VIXCLS",                    # 공포지수
        "10Y_Treasury": "DGS10",            # 10년물 국채
        "FCI": "NFCI",                      # 금융상황지수
        "HY_Spread": "BAMLH0A0HYM2",        # 하이일드 스프레드
        "Dollar_Index": "DTWEXBGS",         # 달러 인덱스 (월간)
    }

    results = {}

    for name, series_id in indicators.items():
        print(f"조회 중: {name} ({series_id})...")
        df = client.get_series(series_id, start_date=start_date)
        if df is not None:
            results[name] = df
            print(f"  ✓ {len(df)}개 데이터 포인트")
        else:
            print(f"  ✗ 실패")

    return results


def save_to_csv(data_dict, output_dir="../data"):
    """
    데이터를 CSV 파일로 저장

    Args:
        data_dict: get_all_indicators() 반환값
        output_dir: 저장 디렉토리
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for name, df in data_dict.items():
        filename = f"{output_dir}/{name}_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"저장: {filename}")


if __name__ == "__main__":
    print("=" * 50)
    print("FRED API 데이터 수집 시작")
    print("=" * 50)

    # 모든 지표 수집
    data = get_all_indicators(days=30)

    print("\n" + "=" * 50)
    print("최신 값 요약")
    print("=" * 50)

    # 최신 값 출력
    for name, df in data.items():
        if len(df) > 0:
            latest = df.iloc[-1]
            print(f"{name:15} : {latest['value']:8.2f}  ({latest['date'].strftime('%Y-%m-%d')})")

    # CSV 저장
    print("\n" + "=" * 50)
    print("CSV 저장 중...")
    print("=" * 50)
    save_to_csv(data)

    print("\n✓ 완료!")
