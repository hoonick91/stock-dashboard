# 환경변수 설정 가이드

## ~/.zshrc에 추가할 내용

```bash
# Stock Market API Keys
export FRED_API_KEY="your_fred_api_key_here"
export FMP_API_KEY="your_fmp_api_key_here"
```

## API 키 발급 방법

### 1. FRED API (무료)
1. https://fredaccount.stlouisfed.org/login/secure/ 회원가입
2. API Keys 메뉴에서 발급
3. `FRED_API_KEY`에 복사

### 2. Financial Modeling Prep (무료 250 req/day)
1. https://site.financialmodelingprep.com/register 회원가입
2. Dashboard에서 API Key 확인
3. `FMP_API_KEY`에 복사

## 적용 방법

```bash
# 1. ~/.zshrc 편집
nano ~/.zshrc

# 2. 위 내용 추가 후 저장

# 3. 적용
source ~/.zshrc

# 4. 확인
echo $FRED_API_KEY
echo $FMP_API_KEY
```

## 테스트 실행

```bash
cd llm-wiki/scripts
python test_apis.py
```
