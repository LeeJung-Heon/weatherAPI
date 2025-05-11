from datetime import datetime, timedelta
import json
import pandas as pd
data = pd.read_excel('/Users/leejungheon/Downloads/단기예보지점좌표(위경도)_20241031기준.xlsx')
# print(data.head())

serviceKey = "UwwSvv1zS3mMEr79c_t52A"
base_date = '20250325'
base_time = '0700'
nx = '62'
ny = '122'

input_d = datetime.strptime(base_date + base_time, "%Y%m%d%H%M")
# print(input_d)

input_d = datetime.strptime(base_date + base_time,"%Y%m%d%H%M") - timedelta(hours=1)
# print(input_d)

input_datetime = datetime.strftime(input_d, "%Y%m%d%H%M")
input_date = input_datetime[:-4]
input_time = input_datetime[-4:]

url = f"https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0/getUltraSrtFcst?pageNo=1&numOfRows=1000&dataType=XML&base_date=20210628&base_time=0630&nx=55&ny=127&authKey=UwwSvv1zS3mMEr79c_t52A"
# print(url)
import requests
import urllib3
urllib3.disable_warnings()
response = requests.get(url, verify=False)
res = json.loads(response.text)
print(res)
