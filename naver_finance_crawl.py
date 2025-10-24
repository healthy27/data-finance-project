import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 네이버가 봇을 막지 않도록 User-Agent 지정
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# 수집할 기업 리스트 (네이버 금융 종목코드)
corp_codes = {
    "삼성전자": "005930",
    "현대차": "005380",
    "LG전자": "066570",
    "카카오": "035720",
    "네이버": "035420",
}

rows = []

for corp, code in corp_codes.items():
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    try:
        # 현재가 (가격 정보)
        price_el = soup.select_one("div.today span.blind")
        price = price_el.text.strip() if price_el else None

        # PER, PBR, ROE 정보가 들어있는 표 찾기
        finance_section = soup.select("table td span.blind")

        per, pbr, roe = None, None, None
        if finance_section and len(finance_section) >= 12:
            # 일반적으로 PER, PBR, ROE 순서가 10~12번째쯤
            per = finance_section[-3].text.strip()
            pbr = finance_section[-2].text.strip()
            roe = finance_section[-1].text.strip()

        rows.append({
            "기업명": corp,
            "종목코드": code,
            "현재가": price,
            "PER": per,
            "PBR": pbr,
            "ROE": roe,
        })
        print(f"[OK] {corp} 수집 완료")
    except Exception as e:
        print(f"[FAIL] {corp} 수집 실패 → {e}")

    time.sleep(0.5)

df = pd.DataFrame(rows)
print("\n=== 결과 미리보기 ===")
print(df)

df.to_csv("naver_financial_data.csv", index=False, encoding="utf-8-sig")
print('\nCSV 저장 완료: naver_financial_data.csv')
