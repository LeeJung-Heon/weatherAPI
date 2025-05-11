from datetime import datetime, timedelta
import json
from urllib.parse import quote_plus
import pandas as pd
import requests
import urllib3
data = pd.read_excel('/Users/leejungheon/Downloads/단기예보지점좌표(위경도)_20241031기준.xlsx')
# print(data.head())

serviceKey = "UwwSvv1zS3mMEr79c_t52A"
valid_times = ["0200","0500","0800","1100","1400","1700","2000","2300"]
now = datetime.now()
hhmm = now.strftime("%H%M")
base_time = max(t for t in valid_times if t <= hhmm)
base_date = now.strftime("%Y%m%d")
nx = '62'
ny = '122'

input_d = datetime.strptime(base_date + base_time, "%Y%m%d%H%M")
# print(input_d)

input_d = datetime.strptime(base_date + base_time,"%Y%m%d%H%M") - timedelta(hours=1)
# print(input_d)

input_datetime = datetime.strftime(input_d, "%Y%m%d%H%M")
input_date = input_datetime[:-4]
input_time = input_datetime[-4:]

#초단기실황api - 기온
url = (
    "https://apihub.kma.go.kr/api/typ02/openApi/"
    "VilageFcstInfoService_2.0/getUltraSrtNcst?"
    f"authKey={(serviceKey)}"
    "&pageNo=1&numOfRows=1000"
    "&dataType=JSON"
    f"&base_date={input_date}"
    f"&base_time={input_time}"
    f"&nx={nx}&ny={ny}"
)
#단기예보조회 - 강수 확률, 강수 형태, 하늘 상태, 풍속, 최고/최저 기온
url2 = ("https://apihub.kma.go.kr/api/typ02/openApi/"
        "VilageFcstInfoService_2.0/getVilageFcst?"
        f"authKey={(serviceKey)}"
        "&numOfRows=1000&pageNo=1"
        "&dataType=JSON"
        f"&base_date={input_date}"
        f"&base_time={input_time}"
        f"&nx={nx}&ny={ny}"
)

urllib3.disable_warnings()
#초단기실황
response = requests.get(url)
try:
    res = response.json()
except ValueError:
    print("Non-JSON response received:\n", response.text)
    raise

items = res.get('response', {}) \
           .get('body', {}) \
           .get('items', {}) \
           .get('item', [])

temperature = None
for item in items:
    if item.get('category') == 'T1H':
        temperature = item.get('obsrValue')
        break

obsr_base_date = None
obsr_time = None
for item in items:
    if item.get('category') == 'T1H':
        obsr_base_date = item.get('baseDate')
        obsr_time = item.get('baseTime')
        break
# 기온 및 실황 발표시각 출력
if temperature is not None:
        if obsr_base_date and obsr_time:
            year_o = obsr_base_date[:4]
            month_o = obsr_base_date[4:6]
            day_o = obsr_base_date[6:]
            hour_o = obsr_time[:2]
            min_o = obsr_time[2:]
            print(f"기온은 {temperature}도 입니다. (발표시각: {year_o}년 {month_o}월 {day_o}일 {hour_o}시 {min_o}분)")
        else:
            print(f"기온은 {temperature}도 입니다.")
else:
    print("기온 정보를 찾을 수 없습니다.")

#단기예보
#
# 단기예보 with retry logic
res2 = None
for bt in reversed(valid_times):
    url2_try = (
        "https://apihub.kma.go.kr/api/typ02/openApi/"
        "VilageFcstInfoService_2.0/getVilageFcst?"
        f"authKey={quote_plus(serviceKey)}"
        "&numOfRows=1000&pageNo=1"
        "&dataType=JSON"
        f"&base_date={input_date}"
        f"&base_time={bt}"
        f"&nx={nx}&ny={ny}"
    )
    r = requests.get(url2_try)
    try:
        tmp = r.json()
    except ValueError:
        print("Non-JSON in retry:\n", r.text)
        continue
    header = tmp.get("response", {}).get("header", {})
    if header.get("resultCode") == "00":
        res2 = tmp
        break
    else:
        print(f"base_time {bt} 반환코드 {header.get('resultCode')} - {header.get('resultMsg')} 재시도합니다.")
if not res2:
    raise RuntimeError("단기예보 데이터를 사용할 수 없습니다.")

# 단기예보 결과 리스트
items2 = res2.get('response', {}) \
           .get('body', {}) \
           .get('items', {}) \
           .get('item', [])

# 초기화
pop = pty = sky = wsd = tmx = tmn = None

# 필요한 항목(category)에 따라 값 저장
for it in items2:
    cat = it.get('category')
    val = it.get('fcstValue')
    # fcstDate, fcstTime 등을 활용해 '오늘' 데이터인지 필터링할 수도 있습니다.
    if cat == 'POP':        # 강수 확률 (%)
        pop = val
    elif cat == 'PTY':      # 강수 형태 (0:없음,1:비,2:비/눈,3:눈,4:소나기)
        # 숫자를 의미있는 문자열로 매핑
        pty_map = {'0':'없음','1':'비','2':'비/눈','3':'눈','4':'소나기'}
        pty = pty_map.get(val, val)
    elif cat == 'SKY':      # 하늘 상태 (1:맑음,2:구름많음,3:흐림,4:흐리고 비)
        sky_map = {'1':'맑음','2':'구름많음','3':'흐림','4':'흐리고 비'}
        sky = sky_map.get(val, val)
    elif cat == 'WSD':      # 풍속 (m/s)
        wsd = val
    elif cat == 'TMX':      # 일 최고 기온 (일단기예보에서만 제공)
        tmx = val
    elif cat == 'TMN':      # 일 최저 기온
        tmn = val

# 출력 포맷
# 강수확률, 강수형태, 하늘상태, 풍속, 일 최저/최고 기온
output = (
    f"강수 확률: {pop}%  "
    f"강수 형태: {pty}  "
    f"하늘 상태: {sky}  "
    f"풍속: {wsd}m/s  "
    f"일 최저/최고 기온: {tmn}°/{tmx}°"
)
# 단기예보 발표시각 추가 및 출력
forecast_base_date = items2[0].get('baseDate') if items2 else None
forecast_base_time = items2[0].get('baseTime') if items2 else None
if forecast_base_date and forecast_base_time:
    year_f = forecast_base_date[:4]
    month_f = forecast_base_date[4:6]
    day_f = forecast_base_date[6:]
    hour_f = forecast_base_time[:2]
    min_f = forecast_base_time[2:]
    output += f" (발표시각: {year_f}년 {month_f}월 {day_f}일 {hour_f}시 {min_f}분)"

print(output)

