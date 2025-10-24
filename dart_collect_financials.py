import requests
import pandas as pd
import time

# 🔑 DART API 키
api_key = "baca1efa60a393ebd217e08e1f2ed5b83836e898"

# 📊 분석할 기업 목록
target_names = ["삼성전자", "현대자동차", "기아", "포스코홀딩스", "LG화학"]
years = [2022, 2023]

# 📁 기업 코드 목록 불러오기
corp_df = pd.read_csv("dart_corp_codes.csv")

def find_corp_code(name: str) -> str | None:
    """기업 이름으로 DART 코드 찾기"""
    normalized_name = (
        name.replace("㈜", "")
        .replace("(주)", "")
        .replace("주식회사", "")
        .replace(" ", "")
        .lower()
    )

    for _, row in corp_df.iterrows():
        corp_name = (
            str(row["corp_name"])
            .replace("㈜", "")
            .replace("(주)", "")
            .replace("주식회사", "")
            .replace(" ", "")
            .lower()
        )
        if normalized_name in corp_name or corp_name in normalized_name:
            return row["corp_code"]
    return None

def to_num(x):
    """숫자 변환"""
    if x is None:
        return None
    x = str(x).replace(",", "").strip()
    return float(x) if x and x != "-" else None

def fetch_financials(corp_code: str, year: int) -> dict:
    """재무 데이터 가져오기 (개선 버전)"""
    
    # 찾을 계정과목들 (다양한 표기 포함)
    account_mapping = {
        "매출액": ["매출액", "수익(매출액)", "영업수익"],
        "영업이익": ["영업이익", "영업이익(손실)"],
        "당기순이익": ["당기순이익", "당기순이익(손실)", "지배기업 소유주지분 순이익"]
    }
    
    # 보고서 종류 (사업보고서 우선)
    reports = ["11011", "11012", "11013", "11014"]
    
    # CFS(연결), OFS(별도) 둘 다 시도
    fs_divs = ["CFS", "OFS"]
    
    result = {}
    
    for rep in reports:
        for fs_div in fs_divs:
            # 전체 재무제표 데이터 가져오기
            url = (
                f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
                f"?crtfc_key={api_key}&corp_code={corp_code}&bsns_year={year}"
                f"&reprt_code={rep}&fs_div={fs_div}"
            )
            
            try:
                r = requests.get(url, timeout=15).json()
                
                if r.get("status") != "000":
                    continue
                
                # 포괄손익계산서만 필터링
                items = [item for item in r.get("list", []) 
                        if "포괄손익계산서" in item.get("sj_nm", "")]
                
                if not items:
                    continue
                
                # 각 계정과목 찾기
                for key, variants in account_mapping.items():
                    if key in result:  # 이미 찾았으면 스킵
                        continue
                    
                    for item in items:
                        account = item.get("account_nm", "")
                        for variant in variants:
                            if variant in account:
                                value = to_num(item.get("thstrm_amount"))
                                if value is not None:
                                    result[key] = value
                                    break
                        if key in result:
                            break
                
                # 세 항목 다 찾았으면 종료
                if len(result) == 3:
                    print(f"  ✓ {year}년 데이터 수집 성공 (보고서: {rep}, 구분: {fs_div})")
                    return result
                    
            except Exception as e:
                print(f"  [ERROR] {year}년 {rep} {fs_div}: {e}")
                continue
            
            time.sleep(0.3)  # API 호출 간격
    
    if not result:
        print(f"  ✗ {year}년 데이터 없음")
    elif len(result) < 3:
        print(f"  △ {year}년 부분 데이터만 수집: {list(result.keys())}")
    
    return result

# -----------------------------
# 데이터 수집 및 처리
# -----------------------------
records = []

for name in target_names:
    code = find_corp_code(name)
    if not code:
        print(f"\n[WARN] 기업코드 못 찾음: {name}")
        continue

    print(f"\n📊 {name} ({code})")
    prev = None
    
    for y in years:
        data = fetch_financials(code, y)
        
        rec = {
            "기업명": name,
            "연도": y,
            "매출액": data.get("매출액"),
            "영업이익": data.get("영업이익"),
            "당기순이익": data.get("당기순이익"),
            "매출액성장률(%)": None,
            "순이익성장률(%)": None,
        }

        # 성장률 계산
        if prev:
            if prev.get("매출액") and data.get("매출액"):
                rec["매출액성장률(%)"] = round(
                    (data["매출액"] - prev["매출액"]) / prev["매출액"] * 100, 2
                )
            if prev.get("당기순이익") and data.get("당기순이익"):
                rec["순이익성장률(%)"] = round(
                    (data["당기순이익"] - prev["당기순이익"]) / prev["당기순이익"] * 100, 2
                )

        records.append(rec)
        prev = data

# ✅ 결과 저장
df = pd.DataFrame(records)
df.to_csv("dart_financials_summary.csv", index=False, encoding="utf-8-sig")

print("\n" + "="*60)
print("✅ 재무 요약 저장 완료: dart_financials_summary.csv")
print("="*60)
print(df.to_string(index=False))