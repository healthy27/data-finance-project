import requests
import zipfile
import xml.etree.ElementTree as ET

# DART API Key
api_key = "baca1efa60a393ebd217e08e1f2ed5b83836e898"

# 1️⃣ 고유번호 파일 다운로드
url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
res = requests.get(url)

# 2️⃣ 압축 파일로 저장
with open("corp_code.zip", "wb") as f:
    f.write(res.content)

# 3️⃣ 압축 해제
with zipfile.ZipFile("corp_code.zip", "r") as zip_ref:
    zip_ref.extractall(".")

# 4️⃣ XML 파싱 → CSV로 저장
tree = ET.parse("CORPCODE.xml")
root = tree.getroot()

rows = []
for child in root.findall("list"):
    rows.append({
        "corp_code": child.find("corp_code").text,
        "corp_name": child.find("corp_name").text,
        "stock_code": child.find("stock_code").text,
        "modify_date": child.find("modify_date").text
    })

import pandas as pd
df = pd.DataFrame(rows)
df.to_csv("dart_corp_codes.csv", index=False, encoding="utf-8-sig")

print("✅ dart_corp_codes.csv 생성 완료!")
print(df.head())
