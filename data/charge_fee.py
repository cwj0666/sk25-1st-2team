# ## 전기차 충전 서비스 요금 현황
# 1. 충전 서비스 요금 데이터 크롤링
import requests
charge_info_url = "https://chargeinfo.ksga.org/ws/" # 차지인포 전기차 충전 서비스 요금 현황 baseline url
org_url = charge_info_url + "organization/company/list?bid=" # 회사 정보 url
tariff_url = charge_info_url + "tariff/charger/list/bidGroup?customerType=" # 충전요금 정보 url

org_r = requests.get(org_url) # 회사 정보 requests
tariff_r = requests.get(tariff_url) # 충전요금 정보 requests

import pandas as pd
org_df = pd.DataFrame(org_r.json()['result']) # 회사 정보
tariff_df = pd.DataFrame(tariff_r.json()) # 충전요금 정보

# 양쪽 DataFrame 모두 'bid' column이 차지인포 사이트에서 기업명을 구분하는 기업code
# 따라서 merge를 'bid' column 중심으로 진행함.
charge_df = pd.merge(org_df, tariff_df, how = 'inner', left_on = 'bid', right_on = 'bid')
# companyName : 충전소 업체명
# bid : 기업코드
# customerType : M - 회원가, G - 비회원가
# averageFee : 26-01-25 기준 전국 해당 업체의 모든 충전소 평균가
charge_df = charge_df[['companyName', 'bid', 'customerType', 'averageFee']].copy()

# 충전소의 비회원가 가격이 아니라 회원가 가격 정보만 extract
# 어차피 전기차 이용자면 보통 본인이 주로 이용하는 충전소에 가입된 회원일 것이기 때문에
# 회원가 가격 기준으로 가격 정보를 가져옴
charge_df2 = charge_df[charge_df.customerType == 'M'].reset_index()
charge_df2 = charge_df2[['companyName', 'bid', 'averageFee']]
charge_df2


# 2. DB 연결 및 저장
import MySQLdb

# SKN_25기 2팀 전용 DB 정보
conn = MySQLdb.connect(host='175.196.76.209', user='sk25_team2', passwd='Encore7277!', db='team2')
cursor = conn.cursor()

# Create Talbe
sql_create = '''
CREATE TABLE charge_fee (
   companyName VARCHAR(100) NOT NULL,   # 충전소 업체명
   bid VARCHAR(50) NOT NULL,            # 기업코드
   averageFee FLOAT(10, 2) NOT NULL,    # 업체별 충전소 평균 가격(26-01-15 기준)
   primary key (bid, companyName)
)
'''
cursor.execute(sql_create) # 테이블 생성

# Insert Data into Table
sql_insert = "INSERT INTO charge_fee VALUES (%s, %s, %s)"
for row_data in charge_df2.values.tolist():
    try:
        cursor.execute(sql_insert, row_data)
    except Exception as e:
        print(row_data)
        print(e)    

conn.commit()

