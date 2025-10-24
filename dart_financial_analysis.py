import requests
import pandas as pd
import time

# ============================================
# 🔑 DART API 키 입력 (반드시 본인 키로 교체!)
# ============================================
api_key = "baca1efa60a393ebd217e08e1f2ed5b83836e898"

# ============================================
# 📊 분석할 기업 목록 (기업명: DART 기업코드)
# ============================================
corp_codes = {
    "삼성전자": "00126380",
    "현대자동차": "00164779",
    "기아": "00117441",
    "포스코홀딩스": "00126381",
    "LG화학": "00137902"
}

years = [2022, 2023]
all_results = []

# ============================================
# 🧩 함수: DART 전체 재무제표 불러오기
# ============================================
def fetch_financials(corp_code, year, fs_div):
    """특정 기업·연도·재무제표 구분(CFS/OFS)에 따른 전체 재무데이터 가져오기"""
    url = (
        f"https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json?"
        f"crtfc_key={api_key}&corp_code={corp_code}&bsns_year={year}"
        f"&reprt_code=11011&fs_div={fs_div}"
    )
    res = requests.get(url, timeout=15).json()
    if res.get("status") != "000" or "list" not in res:
        return pd.DataFrame()
    df = pd.DataFrame(res["list"])
    df["year"] = year
    df["fs_div"] = fs_div
    return df

# ============================================
# 📚 주요 계정명 키워드 (필요한 재무항목 자동 필터)
# ============================================
keywords = [
    "매출", "영업이익", "순이익", "연구개발", "유형자산",
    "부채총계", "자본총계", "수익", "CAPEX"
]

# ============================================
# 🚀 데이터 수집 시작
# ============================================
for name, code in corp_codes.items():
    print(f"\n📊 {name} ({code}) 데이터 수집 중...")
    all_data = []

    for year in years:
        for fs in ["CFS", "OFS"]:  # 연결 / 별도 둘 다 시도
            df = fetch_financials(code, year, fs)
            if not df.empty:
                all_data.append(df)
        time.sleep(0.5)

    if not all_data:
        print(f"[MISS] {name} 데이터 없음")
        continue

    merged = pd.concat(all_data)
    merged = merged[merged["account_nm"].str.contains("|".join(keywords), na=False)]
    merged = merged.pivot_table(index="account_nm", columns="year", values="thstrm_amount", aggfunc="first")

    # 숫자 변환
    merged = merged.apply(pd.to_numeric, errors="coerce")

    # 전기 대비 증가율 계산
    merged["증감률(%)"] = (merged[2023] - merged[2022]) / merged[2022] * 100

    # 부채비율 계산 (부채총계 / 자본총계 * 100)
    if "부채총계" in merged.index and "자본총계" in merged.index:
        merged.loc["부채비율(%)", 2023] = (merged.loc["부채총계", 2023] / merged.loc["자본총계", 2023]) * 100
        merged.loc["부채비율(%)", 2022] = (merged.loc["부채총계", 2022] / merged.loc["자본총계", 2022]) * 100
        merged.loc["부채비율(%)", "증감률(%)"] = (
            merged.loc["부채비율(%)", 2023] - merged.loc["부채비율(%)", 2022]
        )

    merged["기업명"] = name
    all_results.append(merged)

# ============================================
# 📈 전체 기업 통합 + 보기 좋게 출력
# ============================================
final_df = pd.concat(all_results)
final_df.reset_index(inplace=True)

# 숫자 포맷 설정 (지수 → 천단위 콤마)
pd.set_option('display.float_format', '{:,.0f}'.format)
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 150)

print("\n✅ 기업별 재무 성장 요약\n")
print(final_df[['기업명', 'account_nm', 2022, 2023, '증감률(%)']])

# ============================================
# 💾 CSV & 엑셀 저장
# ============================================
final_df.to_csv("dart_financial_growth.csv", index=False, encoding="utf-8-sig")
final_df.to_excel("dart_financial_growth.xlsx", index=False)
print("\n💾 CSV / XLSX 저장 완료: dart_financial_growth.*")
