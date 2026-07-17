"""
개선된 일일 모니터링 대시보드 생성기
- 거시경제: 상단 요약
- 개별 종목: 상세 메인 뷰
- 종목 선택 드롭다운 준비
"""

import pandas as pd
import os
from datetime import datetime


def get_indicator_info():
    """지표 설명 및 계산 방법"""
    return {
        # 거시경제 지표
        "VIX": {
            "description": "시장 변동성 예상 지수",
            "calculation": "FRED",
            "interpretation": "VIX가 20 미만이면 시장이 안정적이며 투자자들의 불안 심리가 낮은 상태입니다. 20-30 사이는 경계 국면으로 변동성이 증가하고 있습니다. 30 이상은 공포 국면으로 시장이 크게 흔들릴 가능성이 높습니다. 역사적으로 VIX가 극단적으로 높을 때가 매수 기회일 수 있습니다."
        },
        "10Y_Treasury": {
            "description": "미국 10년물 국채 금리",
            "calculation": "FRED",
            "interpretation": "금리 상승은 경제 성장 기대와 인플레이션 우려를 반영합니다. 금리가 높아지면 채권 수익률이 증가해 주식 투자 매력도가 상대적으로 감소할 수 있습니다. 연준의 금리 정책 방향을 가늠하는 핵심 지표입니다."
        },
        "FCI": {
            "description": "금융상황지수",
            "calculation": "FRED",
            "interpretation": "음수 값은 금융 환경이 평균보다 완화적임을 의미하며 주식 시장에 긍정적입니다. 양수 값은 금융 긴축을 나타내며, 자금 조달이 어려워지고 경제 활동이 둔화될 수 있습니다."
        },
        "HY_Spread": {
            "description": "하이일드 스프레드",
            "calculation": "FRED",
            "interpretation": "정크본드와 국채 간 금리 차이로 신용 위험을 측정합니다. 5% 미만은 투자자들이 위험을 낮게 평가하는 양호한 환경입니다. 5-7%는 경계 국면, 7% 이상은 기업 부도 위험이 증가하는 위험 신호입니다."
        },
        "sma_50": {
            "description": "50일 이동평균선",
            "calculation": "FMP Quote API의 priceAvg50 필드",
            "formula": "최근 50일간 종가의 평균",
            "interpretation": "최근 50일간의 평균 주가로 단기 추세를 나타냅니다. 주가가 50일선 위에 있으면 단기 상승 추세, 아래에 있으면 하락 추세로 판단합니다."
        },
        "divergence_50": {
            "description": "50일 이평선 이격도",
            "calculation": "현재가와 50일 이평선 비교",
            "formula": "(현재가 ÷ 50일 이평선) × 100",
            "interpretation": "현재가가 50일 이평선에서 얼마나 떨어져 있는지를 %로 나타냅니다. 95-105% 범위가 정상이며, 110% 이상이면 단기 과열, 90% 이하면 과도한 하락입니다."
        },
        "sma_200": {
            "description": "200일 이동평균선",
            "calculation": "FMP Quote API의 priceAvg200 필드",
            "formula": "최근 200일간 종가의 평균",
            "interpretation": "최근 200일간의 평균 주가로 장기 추세를 나타냅니다. 주가가 200일선 위에서 거래되면 강세장(bull market), 아래에서 거래되면 약세장(bear market)으로 봅니다."
        },
        "divergence_200": {
            "description": "200일 이평선 이격도",
            "calculation": "현재가와 200일 이평선 비교",
            "formula": "(현재가 ÷ 200일 이평선) × 100",
            "interpretation": "장기 추세 대비 현재 주가 위치를 나타냅니다. 100% 이상이면 장기 상승 추세, 100% 미만이면 하락 추세입니다."
        },
        "rsi": {
            "description": "상대강도지수 (14일)",
            "calculation": "Alpha Vantage",
            "interpretation": "최근 14일간 상승과 하락의 상대적 강도를 0-100 사이 값으로 나타냅니다. 70 이상은 과매수 구간으로 조정 가능성이 있고, 30 이하는 과매도 구간으로 반등 가능성이 있습니다."
        },
        "per": {
            "description": "주가수익비율",
            "calculation": "FMP key-metrics-ttm API",
            "formula": "1 ÷ earningsYieldTTM (또는 주가 ÷ 주당순이익)",
            "interpretation": "주가를 주당순이익으로 나눈 값으로, 현재 수익 대비 주가가 몇 배인지를 나타냅니다. 업종별로 차이가 있지만, 일반적으로 15-20배가 적정 수준입니다."
        },
        "peg": {
            "description": "주가수익성장비율",
            "calculation": "FMP ratios-ttm API",
            "formula": "PER ÷ 이익 성장률 (priceToEarningsGrowthRatioTTM)",
            "interpretation": "PER을 이익 성장률로 나눈 값으로, 성장성까지 고려한 밸류에이션 지표입니다. 1.0 미만이면 성장 대비 저평가, 1.0 이상이면 고평가로 봅니다."
        },
        "roe": {
            "description": "자기자본이익률",
            "calculation": "FMP key-metrics-ttm API",
            "formula": "(당기순이익 ÷ 자기자본) × 100 (returnOnEquityTTM)",
            "interpretation": "기업이 자기자본으로 얼마나 효율적으로 이익을 창출하는지 나타냅니다. 일반적으로 15% 이상이면 우수한 수익성으로 평가됩니다."
        }
    }


def format_number(value, format_type="number"):
    """숫자 포맷팅"""
    if pd.isna(value) or value is None:
        return "N/A"

    if format_type == "currency":
        return f"${value:,.2f}"
    elif format_type == "currency_billions":
        return f"${value/1e9:,.1f}B"
    elif format_type == "percent":
        return f"{value:.2f}%"
    elif format_type == "number":
        return f"{value:,.2f}"
    elif format_type == "large_number":
        if value >= 1e12:
            return f"${value/1e12:,.2f}T"
        elif value >= 1e9:
            return f"${value/1e9:,.2f}B"
        else:
            return f"${value/1e6:,.2f}M"
    return str(value)


def generate_html_dashboard(csv_file, output_file=None):
    """CSV 파일로부터 개선된 HTML 대시보드 생성"""

    # CSV 읽기
    df = pd.read_csv(csv_file)
    if len(df) == 0:
        print("데이터가 없습니다.")
        return

    row = df.iloc[0]
    indicator_info = get_indicator_info()

    # 출력 파일명 설정
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/dashboard_{row.get('symbol', 'UNKNOWN')}_{timestamp}.html"

    symbol = row.get('symbol', 'N/A')
    company_name = row.get('company_name', symbol)

    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{symbol} - Stock Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header */
        .header {{
            background: white;
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header h1 {{
            font-size: 1.8em;
            color: #2c3e50;
            font-weight: 600;
        }}

        .header .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}

        /* 거시경제 요약 배너 */
        .macro-summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px 32px;
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}

        .macro-title {{
            color: white;
            font-size: 0.9em;
            margin-bottom: 12px;
            opacity: 0.9;
            font-weight: 500;
        }}

        .macro-indicators {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
        }}

        .macro-item {{
            position: relative;
        }}

        .macro-label {{
            color: rgba(255,255,255,0.85);
            font-size: 0.75em;
            margin-bottom: 4px;
        }}

        .macro-value {{
            color: white;
            font-size: 1.2em;
            font-weight: 700;
        }}

        .macro-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.7em;
            margin-left: 6px;
            background: rgba(255,255,255,0.25);
        }}

        /* 종목 메인 카드 */
        .stock-main {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 24px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }}

        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 32px;
        }}

        .stock-info {{
            flex: 1;
        }}

        .stock-symbol {{
            font-size: 2.5em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 8px;
        }}

        .stock-company {{
            font-size: 1.1em;
            color: #7f8c8d;
        }}

        .stock-price {{
            text-align: right;
        }}

        .price-current {{
            font-size: 3.5em;
            font-weight: 700;
            color: #2c3e50;
            line-height: 1;
        }}

        .price-change {{
            font-size: 1.4em;
            font-weight: 600;
            margin-top: 8px;
        }}

        .price-change.positive {{
            color: #27ae60;
        }}

        .price-change.negative {{
            color: #e74c3c;
        }}

        .market-cap {{
            margin-top: 12px;
            color: #7f8c8d;
            font-size: 1em;
        }}

        /* 지표 그리드 */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}

        .metric-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid #e8ebed;
        }}

        .metric-card-header {{
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }}

        .metric-title {{
            font-size: 0.9em;
            color: #7f8c8d;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .info-icon {{
            display: inline-block;
            width: 16px;
            height: 16px;
            line-height: 16px;
            text-align: center;
            background: #667eea;
            color: white;
            border-radius: 50%;
            font-size: 11px;
            font-weight: bold;
            margin-left: 8px;
            cursor: help;
            position: relative;
        }}

        .tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background: #2c3e50;
            color: white;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.85em;
            line-height: 1.6;
            white-space: normal;
            width: 320px;
            max-width: 90vw;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            z-index: 1000;
            transition: opacity 0.2s, visibility 0.2s;
            text-align: left;
        }}

        .tooltip::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -6px;
            border-width: 6px;
            border-style: solid;
            border-color: #2c3e50 transparent transparent transparent;
        }}

        .info-icon:hover .tooltip {{
            visibility: visible;
            opacity: 1;
        }}

        .tooltip-label {{
            font-weight: 600;
            color: #fbbf24;
            display: block;
            margin: 8px 0 4px 0;
        }}

        .tooltip-label:first-child {{
            margin-top: 0;
        }}

        .metric-value {{
            font-size: 2.2em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 8px;
        }}

        .metric-label {{
            font-size: 0.85em;
            color: #95a5a6;
        }}

        .metric-status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
            margin-top: 8px;
        }}

        .status-good {{
            background: #d4edda;
            color: #155724;
        }}

        .status-warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .status-danger {{
            background: #f8d7da;
            color: #721c24;
        }}

        .status-neutral {{
            background: #e2e8f0;
            color: #475569;
        }}

        /* MA 비교 차트 */
        .ma-comparison {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin-bottom: 24px;
        }}

        .ma-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
        }}

        .ma-bars {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .ma-bar-item {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .ma-bar-label {{
            min-width: 100px;
            font-size: 0.9em;
            color: #7f8c8d;
            font-weight: 500;
        }}

        .ma-bar-container {{
            flex: 1;
            height: 32px;
            background: #ecf0f1;
            border-radius: 16px;
            position: relative;
            overflow: hidden;
        }}

        .ma-bar-fill {{
            height: 100%;
            border-radius: 16px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            padding: 0 12px;
            color: white;
            font-weight: 600;
            font-size: 0.85em;
        }}

        .ma-bar-value {{
            min-width: 80px;
            text-align: right;
            font-weight: 600;
            color: #2c3e50;
        }}

        /* RSI 게이지 */
        .rsi-gauge {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}

        .gauge-container {{
            position: relative;
            height: 120px;
            margin: 20px 0;
        }}

        .gauge-bg {{
            width: 100%;
            height: 20px;
            background: linear-gradient(90deg,
                #27ae60 0%,
                #f39c12 30%,
                #95a5a6 50%,
                #f39c12 70%,
                #e74c3c 100%);
            border-radius: 10px;
            position: relative;
        }}

        .gauge-marker {{
            position: absolute;
            top: -40px;
            transform: translateX(-50%);
            text-align: center;
        }}

        .gauge-value {{
            font-size: 2em;
            font-weight: 700;
            color: #2c3e50;
        }}

        .gauge-arrow {{
            width: 0;
            height: 0;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-top: 12px solid #2c3e50;
            margin: 4px auto;
        }}

        .gauge-labels {{
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 0.85em;
            color: #7f8c8d;
        }}

        @media (max-width: 768px) {{
            .stock-header {{
                flex-direction: column;
                gap: 24px;
            }}

            .stock-price {{
                text-align: left;
            }}

            .metrics-grid {{
                grid-template-columns: 1fr;
            }}

            .macro-indicators {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 Stock Market Dashboard</h1>
            <div class="timestamp">{row.get('date', 'N/A')}</div>
        </div>

        <!-- 거시경제 요약 -->
        <div class="macro-summary">
            <div class="macro-title">📈 Market Overview</div>
            <div class="macro-indicators">
"""

    # 거시경제 지표 요약 - 모든 지표 포함
    macro_items = [
        ("VIX", "VIX", "number", 20, 30),
        ("10Y_Treasury", "10Y Rate", "percent", 3, 5),
        ("FCI", "FCI", "number", -1, 0),
        ("HY_Spread", "HY Spread", "percent", 5, 7),
        ("Dollar_Index", "Dollar Index", "number", 100, 120),
        ("Margin_Debt", "Margin Debt", "currency_billions", 500, 700),
        ("Above_MA_Ratio", "Above MA(200)", "percent", 30, 70),
    ]

    for key, label, fmt, warn_threshold, danger_threshold in macro_items:
        if key in row and not pd.isna(row[key]):
            value = row[key]
            formatted_value = format_number(value, fmt)

            # 상태 판단
            status = ""
            if key == "VIX":
                if value < warn_threshold:
                    status = "안정"
                elif value < danger_threshold:
                    status = "경계"
                else:
                    status = "공포"
            elif key == "FCI":
                status = "완화" if value < 0 else "긴축"
            elif key in ["HY_Spread", "10Y_Treasury"]:
                if value < warn_threshold:
                    status = "양호"
                elif value < danger_threshold:
                    status = "경계"
                else:
                    status = "위험"
            elif key == "Above_MA_Ratio":
                if value >= 70:
                    status = "강세"
                elif value <= 30:
                    status = "약세"
                else:
                    status = "중립"
            elif key == "Margin_Debt":
                status = "분기별"
            elif key == "Dollar_Index":
                if value > 110:
                    status = "강세"
                else:
                    status = "약세"

            html += f"""
                <div class="macro-item">
                    <div class="macro-label">{label}</div>
                    <div class="macro-value">
                        {formatted_value}
                        {"<span class='macro-badge'>" + status + "</span>" if status else ""}
                    </div>
                </div>
"""

    html += """
            </div>
        </div>

        <!-- 종목 메인 카드 -->
        <div class="stock-main">
            <div class="stock-header">
                <div class="stock-info">
                    <div class="stock-symbol">""" + symbol + """</div>
                    <div class="stock-company">""" + company_name + """</div>
                </div>
                <div class="stock-price">
"""

    # 가격 정보
    if 'price' in row and not pd.isna(row['price']):
        price = row['price']
        change_pct = row.get('change_percent', 0)
        change_class = "positive" if change_pct >= 0 else "negative"
        change_sign = "▲" if change_pct >= 0 else "▼"

        html += f"""
                    <div class="price-current">${price:,.2f}</div>
                    <div class="price-change {change_class}">{change_sign} {abs(change_pct):.2f}%</div>
"""
    else:
        html += """
                    <div class="price-current">N/A</div>
                    <div class="price-change">데이터 없음</div>
"""

    # 시가총액
    if 'market_cap' in row and not pd.isna(row['market_cap']):
        mcap_formatted = format_number(row['market_cap'], 'large_number')
        html += f"""
                    <div class="market-cap">시가총액: {mcap_formatted}</div>
"""

    html += """
                </div>
            </div>
        </div>

        <!-- 이동평균 비교 -->
        <div class="ma-comparison">
            <div class="ma-title">📊 Moving Average Analysis</div>
            <div class="ma-bars">
"""

    # MA 바 차트
    if 'price' in row and not pd.isna(row['price']):
        current_price = row['price']

        ma_data = [
            ("현재가", current_price, "#667eea", None),
            ("50일 이평", row.get('sma_50'), "#3498db", row.get('divergence_50')),
            ("200일 이평", row.get('sma_200'), "#e74c3c", row.get('divergence_200')),
        ]

        max_value = max([v for _, v, _, _ in ma_data if v and not pd.isna(v)], default=1)

        for label, value, color, divergence in ma_data:
            if value and not pd.isna(value):
                width_pct = (value / max_value) * 100
                divergence_text = ""
                if divergence and not pd.isna(divergence):
                    div_status = ""
                    if divergence > 105:
                        div_status = "과열"
                    elif divergence < 95:
                        div_status = "과매도"
                    else:
                        div_status = "정상"
                    divergence_text = f" • 이격도: {divergence:.1f}% ({div_status})"

                html += f"""
                <div class="ma-bar-item">
                    <div class="ma-bar-label">{label}{divergence_text}</div>
                    <div class="ma-bar-container">
                        <div class="ma-bar-fill" style="width: {width_pct}%; background: {color};">
                            ${value:,.2f}
                        </div>
                    </div>
                    <div class="ma-bar-value">${value:,.2f}</div>
                </div>
"""

    # 이격도 계산 공식 설명
    html += """
                <div style="margin-top: 16px; padding: 12px; background: #f8f9fa; border-radius: 8px; font-size: 0.85em; color: #6c757d;">
                    <strong>💡 이격도 계산:</strong> (현재가 ÷ 이동평균) × 100<br>
                    95-105% 범위가 정상, 그 외는 과열 또는 과매도 상태
                </div>
            </div>
        </div>

        <!-- RSI 게이지 -->
"""

    if 'rsi' in row and not pd.isna(row['rsi']):
        rsi_value = row['rsi']
        rsi_position = rsi_value  # 0-100

        html += f"""
        <div class="rsi-gauge">
            <div class="ma-title">🎯 RSI (Relative Strength Index)</div>
            <div class="gauge-container">
                <div class="gauge-marker" style="left: {rsi_position}%;">
                    <div class="gauge-value">{rsi_value:.1f}</div>
                    <div class="gauge-arrow"></div>
                </div>
                <div class="gauge-bg"></div>
                <div class="gauge-labels">
                    <span>0 (과매도)</span>
                    <span>30</span>
                    <span>50</span>
                    <span>70</span>
                    <span>100 (과매수)</span>
                </div>
            </div>
        </div>
"""

    html += """
        <!-- 재무 지표 -->
        <div class="metrics-grid">
"""

    # 재무 지표 카드
    financial_metrics = [
        ("per", "P/E Ratio", "number", "주가수익비율"),
        ("peg", "PEG Ratio", "number", "주가수익성장비율"),
        ("roe", "ROE", "percent", "자기자본이익률"),
    ]

    for key, title, fmt, description in financial_metrics:
        if key in row and not pd.isna(row[key]):
            value = row[key]
            if key == "roe":
                value = value * 100

            formatted_value = format_number(value, fmt)

            # 상태 판단
            status = ""
            status_class = "neutral"

            if key == "peg":
                if value < 1.0:
                    status = "저평가"
                    status_class = "good"
                elif value < 2.0:
                    status = "적정"
                    status_class = "neutral"
                else:
                    status = "고평가"
                    status_class = "warning"
            elif key == "roe":
                if value >= 15:
                    status = "우수"
                    status_class = "good"
                elif value >= 10:
                    status = "양호"
                    status_class = "neutral"
                elif value > 0:
                    status = "보통"
                    status_class = "warning"
                else:
                    status = "손실"
                    status_class = "danger"
            elif key == "per":
                if value < 15:
                    status = "저평가"
                    status_class = "good"
                elif value < 25:
                    status = "적정"
                    status_class = "neutral"
                else:
                    status = "고평가"
                    status_class = "warning"

            # 툴팁 정보
            info = indicator_info.get(key, {})
            description_text = info.get("description", "")
            calculation_text = info.get("calculation", "")
            formula_text = info.get("formula", "")
            interpretation = info.get("interpretation", "")

            html += f"""
            <div class="metric-card">
                <div class="metric-card-header">
                    <div class="metric-title">{title}</div>
"""

            if description_text or calculation_text or formula_text or interpretation:
                html += """                    <span class="info-icon">?
                        <span class="tooltip">
"""
                if description_text:
                    html += f"""                            <span class="tooltip-label">📌 정의</span>
                            {description_text}
"""
                if formula_text:
                    html += f"""                            <span class="tooltip-label">🧮 계산 공식</span>
                            {formula_text}
"""
                if calculation_text:
                    html += f"""                            <span class="tooltip-label">📊 데이터 출처</span>
                            {calculation_text}
"""
                if interpretation:
                    html += f"""                            <span class="tooltip-label">💡 해석</span>
                            {interpretation}
"""
                html += """                        </span>
                    </span>
"""

            html += f"""
                </div>
                <div class="metric-value">{formatted_value}</div>
                <div class="metric-label">{description}</div>
"""

            if status:
                html += f"""
                <div class="metric-status status-{status_class}">{status}</div>
"""

            html += """
            </div>
"""

    html += """
        </div>
    </div>
</body>
</html>
"""

    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    abs_path = os.path.abspath(output_file)
    print(f"✓ 대시보드 생성 완료: {output_file}")

    # 크롬으로 열기
    import subprocess
    try:
        subprocess.run(["open", "-a", "Google Chrome", abs_path], check=True)
        print(f"✓ 크롬에서 대시보드 열림")
    except:
        pass

    return output_file


def main():
    """메인 실행"""
    import sys

    data_dir = "../data"

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # 가장 최근 daily_report 파일 찾기
        import glob
        csv_files = glob.glob(f"{data_dir}/daily_report_*.csv")
        if not csv_files:
            print("CSV 파일을 찾을 수 없습니다.")
            return
        csv_file = max(csv_files, key=os.path.getmtime)

    print(f"CSV 파일: {csv_file}")
    generate_html_dashboard(csv_file)


if __name__ == "__main__":
    main()
