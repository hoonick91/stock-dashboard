"""
일일 모니터링 대시보드 생성기
CSV 데이터를 HTML 대시보드로 변환
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
            "description": "금융상황지수 (Financial Conditions Index)",
            "calculation": "FRED",
            "interpretation": "음수 값은 금융 환경이 평균보다 완화적임을 의미하며 주식 시장에 긍정적입니다. 양수 값은 금융 긴축을 나타내며, 자금 조달이 어려워지고 경제 활동이 둔화될 수 있습니다. 급격한 변화는 시장 변곡점을 시사합니다."
        },
        "HY_Spread": {
            "description": "하이일드 채권 스프레드",
            "calculation": "FRED",
            "interpretation": "정크본드와 국채 간 금리 차이로 신용 위험을 측정합니다. 5% 미만은 투자자들이 위험을 낮게 평가하는 양호한 환경입니다. 5-7%는 경계 국면, 7% 이상은 기업 부도 위험이 증가하는 위험 신호입니다."
        },
        "Dollar_Index": {
            "description": "달러 인덱스 (DXY)",
            "calculation": "FRED",
            "interpretation": "달러 강세는 미국 수출 기업에 부담이 되며, 신흥국 자산과 원자재 가격에 하방 압력을 줍니다. 반대로 달러 약세는 글로벌 유동성 증가와 위험 자산 선호로 이어질 수 있습니다."
        },
        "Margin_Debt": {
            "description": "증권사 마진 부채 총액",
            "calculation": "FRED (분기별)",
            "interpretation": "투자자들이 빌려서 투자하는 금액입니다. 마진 부채 증가는 낙관론과 위험 선호를 나타내지만, 과도한 증가는 시장 과열 신호일 수 있습니다. 급격한 감소는 강제 청산과 시장 조정의 전조가 될 수 있습니다."
        },
        "Above_MA_Ratio": {
            "description": "200일 이평선 상회 종목 비중",
            "calculation": "FMP (대형주 샘플)",
            "interpretation": "시장 참여도(breadth)를 측정하는 지표입니다. 70% 이상이면 광범위한 강세장, 30% 이하면 약세장입니다. 지수는 상승해도 이 비율이 낮다면 소수 종목만 상승하는 불안정한 랠리일 수 있습니다."
        },

        # 기술적 지표
        "sma_50": {
            "description": "50일 이동평균선",
            "calculation": "FMP Quote",
            "interpretation": "최근 50일간의 평균 주가로 단기 추세를 나타냅니다. 주가가 50일선 위에 있으면 단기 상승 추세, 아래에 있으면 하락 추세로 판단합니다. 50일선이 상승하면서 주가가 그 위에 있을 때 매수 신호로 볼 수 있습니다."
        },
        "divergence_50": {
            "description": "50일 이평선 이격도",
            "calculation": "계산: (현재가 / 50일선) × 100",
            "interpretation": "현재가가 50일 이평선에서 얼마나 떨어져 있는지를 %로 나타냅니다. 95-105% 범위가 정상이며, 110% 이상이면 단기 과열로 조정 가능성이 있고, 90% 이하면 과도한 하락으로 반등 기회일 수 있습니다."
        },
        "sma_200": {
            "description": "200일 이동평균선",
            "calculation": "FMP Quote",
            "interpretation": "최근 200일간의 평균 주가로 장기 추세를 나타냅니다. 주가가 200일선 위에서 거래되면 강세장(bull market), 아래에서 거래되면 약세장(bear market)으로 봅니다. 200일선 돌파는 중요한 매매 신호입니다."
        },
        "divergence_200": {
            "description": "200일 이평선 이격도",
            "calculation": "계산: (현재가 / 200일선) × 100",
            "interpretation": "장기 추세 대비 현재 주가 위치를 나타냅니다. 100% 이상이면 장기 상승 추세, 100% 미만이면 하락 추세입니다. 극단적으로 높거나 낮을 때(120% 이상 또는 80% 이하) 추세 전환 가능성을 주의해야 합니다."
        },
        "rsi": {
            "description": "상대강도지수 (14일)",
            "calculation": "Alpha Vantage",
            "interpretation": "최근 14일간 상승과 하락의 상대적 강도를 0-100 사이 값으로 나타냅니다. 70 이상은 과매수 구간으로 조정 가능성이 있고, 30 이하는 과매도 구간으로 반등 가능성이 있습니다. 50 근처는 중립 구간입니다."
        },

        # 재무 지표
        "market_cap": {
            "description": "시가총액",
            "calculation": "FMP Metrics",
            "interpretation": "기업의 전체 가치를 나타냅니다. 일반적으로 2,000억 달러 이상은 대형주(mega-cap), 100-2,000억은 대형주(large-cap), 20-100억은 중형주(mid-cap), 20억 미만은 소형주(small-cap)로 분류합니다. 규모가 클수록 안정적이지만 성장성은 낮을 수 있습니다."
        },
        "per": {
            "description": "주가수익비율 (PER)",
            "calculation": "FMP Metrics",
            "interpretation": "주가를 주당순이익으로 나눈 값으로, 현재 수익 대비 주가가 몇 배인지를 나타냅니다. 업종별로 차이가 있지만, 일반적으로 15-20배가 적정 수준입니다. 낮을수록 저평가, 높을수록 고평가 또는 높은 성장 기대를 의미할 수 있습니다."
        },
        "peg": {
            "description": "주가수익성장비율 (PEG)",
            "calculation": "FMP Ratios",
            "interpretation": "PER을 이익 성장률로 나눈 값으로, 성장성까지 고려한 밸류에이션 지표입니다. 1.0 미만이면 성장 대비 저평가, 1.0 이상이면 고평가로 봅니다. 성장주 투자 시 PER보다 PEG가 더 유용한 지표입니다."
        },
        "roe": {
            "description": "자기자본이익률 (ROE)",
            "calculation": "FMP Metrics",
            "interpretation": "기업이 자기자본으로 얼마나 효율적으로 이익을 창출하는지 나타냅니다. 일반적으로 15% 이상이면 우수한 수익성으로 평가됩니다. 지속적으로 높은 ROE를 유지하는 기업은 경쟁 우위가 있다고 볼 수 있습니다. 다만 부채 비율도 함께 확인해야 합니다."
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
        return f"${value:,.0f}"
    return str(value)


def get_status_class(indicator, value):
    """상태별 CSS 클래스 반환"""
    if pd.isna(value):
        return ""

    # VIX
    if indicator == "VIX":
        if value < 20:
            return "status-good"
        elif value < 30:
            return "status-warning"
        else:
            return "status-danger"

    # 하이일드 스프레드
    elif indicator == "HY_Spread":
        if value < 5:
            return "status-good"
        elif value < 7:
            return "status-warning"
        else:
            return "status-danger"

    # 금융상황지수
    elif indicator == "FCI":
        if value < 0:
            return "status-good"
        else:
            return "status-warning"

    # RSI
    elif indicator == "rsi":
        if value >= 70:
            return "status-danger"
        elif value <= 30:
            return "status-good"
        else:
            return "status-neutral"

    # 이격도
    elif indicator in ["divergence_50", "divergence_200"]:
        if value > 105:
            return "status-warning"
        elif value < 95:
            return "status-warning"
        else:
            return "status-good"

    # Above MA Ratio
    elif indicator == "Above_MA_Ratio":
        if value >= 70:
            return "status-good"
        elif value <= 30:
            return "status-danger"
        else:
            return "status-neutral"

    return ""


def generate_html_dashboard(csv_file, output_file=None):
    """CSV 파일로부터 HTML 대시보드 생성"""

    # CSV 읽기
    df = pd.read_csv(csv_file)
    if len(df) == 0:
        print("데이터가 없습니다.")
        return

    row = df.iloc[0]

    # 출력 파일명 설정
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/dashboard_{row['symbol']}_{timestamp}.html"

    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>투자 모니터링 대시보드 - {row['symbol']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .header h1 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2em;
        }}

        .header .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .section-title {{
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 20px;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}

        .metric {{
            padding: 16px 0;
            border-bottom: 1px solid #f0f0f0;
        }}

        .metric:last-child {{
            border-bottom: none;
        }}

        .metric-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .metric-label {{
            font-weight: 500;
            color: #555;
        }}

        .metric-value {{
            font-weight: 600;
            font-size: 1.1em;
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
            margin-left: 6px;
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
            background: #333;
            color: white;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 0.88em;
            line-height: 1.7;
            white-space: normal;
            width: 350px;
            max-width: 90vw;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
            z-index: 1000;
            transition: opacity 0.2s, visibility 0.2s;
            text-align: left;
        }}

        .tooltip::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #333 transparent transparent transparent;
        }}

        .info-icon:hover .tooltip {{
            visibility: visible;
            opacity: 1;
        }}

        .tooltip-row {{
            margin: 6px 0;
        }}

        .tooltip-label {{
            font-weight: 600;
            color: #fbbf24;
            display: block;
            margin-bottom: 2px;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 8px;
        }}

        .status-good {{
            color: #10b981;
        }}

        .status-warning {{
            color: #f59e0b;
        }}

        .status-danger {{
            color: #ef4444;
        }}

        .status-neutral {{
            color: #6b7280;
        }}

        .badge-good {{
            background: #d1fae5;
            color: #065f46;
        }}

        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge-danger {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .badge-neutral {{
            background: #e5e7eb;
            color: #374151;
        }}

        .stock-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }}

        .stock-header h2 {{
            font-size: 1.8em;
            margin-bottom: 5px;
        }}

        .stock-header .company {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .price-info {{
            font-size: 2.5em;
            font-weight: 700;
            margin: 10px 0;
        }}

        .price-change {{
            font-size: 1.2em;
            font-weight: 600;
        }}

        .price-change.positive {{
            color: #10b981;
        }}

        .price-change.negative {{
            color: #ef4444;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 일일 투자 모니터링 대시보드</h1>
            <div class="timestamp">생성일시: {row['date']}</div>
        </div>

        <!-- 거시경제 지표 -->
        <div class="section">
            <div class="section-title">🌍 거시경제 환경</div>
"""

    # 지표 정보 가져오기
    indicator_info = get_indicator_info()

    # 거시경제 지표
    macro_indicators = [
        ("VIX", "VIX 지수", "number"),
        ("10Y_Treasury", "10년물 금리", "percent"),
        ("FCI", "금융상황지수", "number"),
        ("HY_Spread", "하이일드 스프레드", "percent"),
        ("Dollar_Index", "달러 인덱스", "number"),
        ("Margin_Debt", "마진 부채", "currency_billions"),
        ("Above_MA_Ratio", "이평선(200일) 상회", "percent"),
    ]

    for key, label, fmt in macro_indicators:
        if key in row and not pd.isna(row[key]):
            value = row[key]
            formatted_value = format_number(value, fmt)
            status_class = get_status_class(key, value)

            # 상태 텍스트
            status_text = ""
            if key == "VIX":
                status_text = "안정" if value < 20 else ("경계" if value < 30 else "공포")
            elif key == "HY_Spread":
                status_text = "양호" if value < 5 else ("경계" if value < 7 else "위험")
            elif key == "FCI":
                status_text = "완화" if value < 0 else "긴축"
            elif key == "Above_MA_Ratio":
                status_text = "강세" if value >= 70 else ("약세" if value <= 30 else "중립")

            badge_class = ""
            if status_class == "status-good":
                badge_class = "badge-good"
            elif status_class == "status-warning":
                badge_class = "badge-warning"
            elif status_class == "status-danger":
                badge_class = "badge-danger"
            else:
                badge_class = "badge-neutral"

            # 지표 정보
            info = indicator_info.get(key, {})
            description = info.get("description", "")
            calculation = info.get("calculation", "")
            interpretation = info.get("interpretation", "")

            html += f"""
            <div class="metric">
                <div class="metric-header">
                    <span class="metric-label">
                        {label}
"""
            # 툴팁 추가
            if description or calculation or interpretation:
                html += """                        <span class="info-icon">?
                            <span class="tooltip">
"""
                if description:
                    html += f"""                                <div class="tooltip-row">
                                    <span class="tooltip-label">📌 설명</span>
                                    {description}
                                </div>
"""
                if calculation:
                    html += f"""                                <div class="tooltip-row">
                                    <span class="tooltip-label">📊 데이터 출처</span>
                                    {calculation}
                                </div>
"""
                if interpretation:
                    html += f"""                                <div class="tooltip-row">
                                    <span class="tooltip-label">💡 해석 기준</span>
                                    {interpretation}
                                </div>
"""
                html += """                            </span>
                        </span>
"""
            html += """                    </span>
                    <span>
                        <span class="metric-value {status_class}">{formatted_value}</span>
""".format(status_class=status_class, formatted_value=formatted_value)
            if status_text:
                html += f"""                        <span class="badge {badge_class}">{status_text}</span>
"""
            html += """                    </span>
                </div>
            </div>
"""

    html += """        </div>

        <!-- 종목 분석 -->
        <div class="stock-header">
"""

    # 종목 헤더
    symbol = row.get('symbol', 'N/A')
    company_name = row.get('company_name', symbol)

    html += f"""            <h2>{symbol}</h2>
            <div class="company">{company_name}</div>
"""

    # 가격 정보 (있는 경우만 표시)
    if 'price' in row and not pd.isna(row['price']):
        price = row['price']
        change_pct = row.get('change_percent', 0)
        change_class = "positive" if change_pct >= 0 else "negative"
        change_sign = "+" if change_pct >= 0 else ""

        html += f"""            <div class="price-info">${price:,.2f}</div>
            <div class="price-change {change_class}">{change_sign}{change_pct:.2f}%</div>
"""
    else:
        html += """            <div class="price-info" style="font-size: 1.2em; opacity: 0.7;">가격 정보 없음</div>
"""

    html += """        </div>

        <div class="grid">
            <!-- 기술적 지표 -->
            <div class="section">
                <div class="section-title">📈 기술적 지표</div>
"""

    # 기술적 지표
    technical = [
        ("sma_50", "50일 이동평균", "currency"),
        ("divergence_50", "50일 이격도", "percent"),
        ("sma_200", "200일 이동평균", "currency"),
        ("divergence_200", "200일 이격도", "percent"),
        ("rsi", "RSI(14)", "number"),
    ]

    for key, label, fmt in technical:
        if key in row and not pd.isna(row[key]):
            value = row[key]
            formatted_value = format_number(value, fmt)
            status_class = get_status_class(key, value)

            status_text = ""
            badge_class = ""

            if key == "rsi":
                rsi_status = row.get("rsi_status", "")
                status_text = rsi_status
                if value >= 70:
                    badge_class = "badge-danger"
                elif value <= 30:
                    badge_class = "badge-good"
                else:
                    badge_class = "badge-neutral"

            # 지표 정보
            info = indicator_info.get(key, {})
            description = info.get("description", "")
            calculation = info.get("calculation", "")
            interpretation = info.get("interpretation", "")

            html += f"""
                <div class="metric">
                    <div class="metric-header">
                        <span class="metric-label">
                            {label}
"""
            # 툴팁 추가
            if description or calculation or interpretation:
                html += """                            <span class="info-icon">?
                                <span class="tooltip">
"""
                if description:
                    html += f"""                                    <div class="tooltip-row">
                                        <span class="tooltip-label">📌 설명</span>
                                        {description}
                                    </div>
"""
                if calculation:
                    html += f"""                                    <div class="tooltip-row">
                                        <span class="tooltip-label">📊 데이터 출처</span>
                                        {calculation}
                                    </div>
"""
                if interpretation:
                    html += f"""                                    <div class="tooltip-row">
                                        <span class="tooltip-label">💡 해석 기준</span>
                                        {interpretation}
                                    </div>
"""
                html += """                                </span>
                            </span>
"""
            html += """                        </span>
                        <span>
                            <span class="metric-value {status_class}">{formatted_value}</span>
""".format(status_class=status_class, formatted_value=formatted_value)
            if status_text:
                html += f"""                            <span class="badge {badge_class}">{status_text}</span>
"""
            html += """                        </span>
                    </div>
                </div>
"""

    html += """            </div>

            <!-- 재무 지표 -->
            <div class="section">
                <div class="section-title">💰 재무 지표</div>
"""

    # 재무 지표
    financial = [
        ("market_cap", "시가총액", "large_number"),
        ("per", "P/E Ratio", "number"),
        ("peg", "PEG Ratio", "number"),
        ("roe", "ROE", "percent"),
    ]

    for key, label, fmt in financial:
        if key in row and not pd.isna(row[key]):
            value = row[key]
            if key == "roe":
                value = value * 100  # ROE는 퍼센트로 변환
            formatted_value = format_number(value, fmt)

            # 지표 정보
            info = indicator_info.get(key, {})
            description = info.get("description", "")
            calculation = info.get("calculation", "")
            interpretation = info.get("interpretation", "")

            html += f"""
                <div class="metric">
                    <div class="metric-header">
                        <span class="metric-label">
                            {label}
"""
            # 툴팁 추가
            if description or calculation or interpretation:
                html += """                            <span class="info-icon">?
                                <span class="tooltip">
"""
                if description:
                    html += f"""                                    <div class="tooltip-row">
                                        <span class="tooltip-label">📌 설명</span>
                                        {description}
                                    </div>
"""
                if calculation:
                    html += f"""                                    <div class="tooltip-row">
                                        <span class="tooltip-label">📊 데이터 출처</span>
                                        {calculation}
                                    </div>
"""
                if interpretation:
                    html += f"""                                    <div class="tooltip-row">
                                        <span class="tooltip-label">💡 해석 기준</span>
                                        {interpretation}
                                    </div>
"""
                html += """                                </span>
                            </span>
"""
            html += f"""                        </span>
                        <span class="metric-value">{formatted_value}</span>
                    </div>
                </div>
"""

    html += """            </div>
        </div>
    </div>
</body>
</html>
"""

    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ 대시보드 생성 완료: {output_file}")
    return output_file


def main():
    """메인 실행"""
    import sys
    import subprocess

    # CSV 파일 찾기
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
    output_file = generate_html_dashboard(csv_file)

    # 크롬으로 자동 열기
    if output_file:
        abs_path = os.path.abspath(output_file)
        print(f"\n크롬으로 여는 중...")
        try:
            subprocess.run(["open", "-a", "Google Chrome", abs_path], check=True)
            print(f"✓ 크롬에서 대시보드 열림")
        except subprocess.CalledProcessError:
            print(f"⚠️  크롬 실행 실패. 수동으로 여세요:")
            print(f"   open -a 'Google Chrome' '{abs_path}'")


if __name__ == "__main__":
    main()
