from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from .models import *
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from datetime import datetime,timedelta
from scipy.stats import norm
import numpy as np
import os
import json
import math
import requests
import pprint
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from keras.models import load_model

#. horimevenv/bin/activate

#피크타임: 2023071424-2023071505
#주의타임: 위 타임 -3시간 / +3시간

#######1. 2023년 7월 14-16일 예천군 보문교 사건 호우#######
####15일 오전 5시 16분쯤 산사태가 발생해 집 5채가 쓸려내려 간 경북 예천군 효자면 백석리

#http로 실행했을 때 오류 방지
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

pp = pprint.PrettyPrinter()

#load api_key from .env
load_dotenv()
youtube_api_key1 = os.getenv('YOUTUBE_API_KEY_1')
youtube_api_key2 = os.getenv('YOUTUBE_API_KEY_2')

#Youtube Geolocation API를 활용하여 로드
def get_current_location():
    # YOUTUBE API 키
    API_KEY = [youtube_api_key1, youtube_api_key2]
    # 현재 위치 요청
    try:
        url = "https://www.googleapis.com/geolocation/v1/geolocate?key={}".format(API_KEY[0])
    except: #API 할당량 다차면 다른 키 가져오기
        url = "https://www.googleapis.com/geolocation/v1/geolocate?key={}".format(API_KEY[1])
    response = requests.post(url)

    # 요청이 성공하면 응답을 처리
    if response.status_code == 200:
        # 위도와 경도를 추출pi
        latitude = response.json()["location"]["lat"]
        longitude = response.json()["location"]["lng"]
        return latitude, longitude
    else:
        # 요청이 실패하면 오류를 출력
        print("요청실패 코드 {} 오류".format(response.status_code))
        return None, None

def get_altitude(lat, lon):
        # YOUTUBE API 키
    API_KEY = [youtube_api_key1, youtube_api_key2]
    # 현재 위치 요청
    url = "https://maps.googleapis.com/maps/api/elevation/json"

    params = {
        "key":API_KEY[0],
        "locations": f"{lat},{lon}",
    }
    response = requests.post(url, params=params)
    # 요청이 성공하면 응답을 처리
    if response.status_code == 200 or response.json()["status"] == "OK":
        # 고도 추출
        alt = response.json()["results"][0]["elevation"]
        return alt
    else:
        # 요청이 실패하면 오류를 출력
        print("요청실패 코드{}오류".format(response.status_code))
        return None

#위도 경도를 주소로 변환
def latalt_to_addr(lat, lon):
    coords = f"{lat},{lon}"
    geolocator = Nominatim(user_agent = 'South Korea')
    location = geolocator.reverse(coords)
    addr = location.address
    addr=addr.split(',')[:-2]
    addr.reverse()
    addr = ' '.join(s for s in addr)
    return addr

#id : 0 - 실시간 수위 | id : 1 - 실시간 댐수문 정보 | id : 2 - 실시간 시간별 강수량
def wamis(dt, id, code):
    #[강수량, 수위, 유입량 iqty, 방류량 tdqty]
    id_desc = ['실시간 시간별 수위', '실시간 시간별 댐수문', '실시간 시간별 강수량']
    wamis_key = ['C232D2B8-2086-41BD-B5D2-082540EFCBF5', 'B8453810-8648-4E5F-B037-97E9A2E61BF4', '6D0F24D5-D144-46FA-8EB8-64E52651721A'] 
    wamis_url = ['http://www.wamis.go.kr:8080/wamis/openapi/wkw/wl_hrdata', 'http://www.wamis.go.kr:8080/wamis/openapi/wkd/mn_hrdata', 'http://www.wamis.go.kr:8080/wamis/openapi/wkw/rf_hrdata']
    
    #id가 0이나 1일때
    obs_code = ["2001685", "2002677", "2004630"]
    dam_code = ['2001110', '2002110', '2004101']
    dam_name = ['안동댐', '임하댐', '영주댐']
    #안동댐으로만 input

    #id가 2일때
    gisang_code = ['20031136', '20041272', '20044070']
    gisang_name = ['경상북도 안동시 기상청', '경상북도 영주시 기상청', '예천군(두천리) 기상청']
    #예천군 두천리 기상청

    #id : 0 - 실시간 수위 | id : 1 - 실시간 댐수문 정보 | id : 2 - 실시간 시간별 강수량
    #id : 0,1 -> 댐 : 0 - 안동, 1 - 임하, 2 - 영주
    #id : 2 -> 기상청 : 0 - 안동시, 1 - 영주시

    result=[]
    params = {'key': wamis_key[id], 'startdt': dt, 'enddt': dt}
    if(id==2):
        params['obscd'] = gisang_code[code]
        request = requests.get(wamis_url[id], params=params)
        contents=request.text
        js = json.loads(contents)
        result.append(js)
        # pp.pprint("<{}> {} 정보: {}".format(gisang_name[code], id_desc[id], js))
    else:
        if(id==0):
            params['obscd'] = obs_code[code]
        elif(id==1):
            params['damcd'] = dam_code[code]
        request = requests.get(wamis_url[id], params=params)
        contents=request.text
        js = json.loads(contents)
        result.append(js)
        # pp.pprint("<{}> {} 정보: {}".format(dam_name[code], id_desc[id], js))
    print('wamis - {} API 호출 완료'.format(id_desc[id]))
    return result

#json에 key가 존재하는지 확인
def is_json_key_present(json, key1, key2):
    try:
        buf = json[key1][key2]
    except KeyError:
        return False

    return True

ow_key = os.getenv('OPENWEATHER_API_KEY')
ow_url = "https://api.openweathermap.org/data/2.5/weather"
def openweather(lat, lon):
    params={'lat':lat, 'lon':lon, 'appid':ow_key, 'lang':'kr'}
    res = requests.get(ow_url, params=params)
    res = json.loads(res.text)
    #현재 기온, 날씨 설명, 최고/최저기온, 강수량(1시간은 front에 보여주고, 3시간은 저장)
    dict = {'temp' : math.ceil(res["main"]["temp"] - 273), #현재 기온
            'desc' : res["weather"][0]["description"], #날씨 설명
            'temp_max' : math.ceil(res["main"]["temp_max"] - 273), #최고기온
            'temp_min' : math.ceil(res["main"]["temp_min"] - 273), #최저기온
            'rain_1h' : 0, #최근 1시간 강수량
            'rain_3h' : 0, #최근 3시간 강수량
            }
    #강수량이 0이면 호출된 JSON데이터 내에 없어서 KeyError남 -> 조건문으로 검사함
    if is_json_key_present(res, 'rain', '1h'):
        dict['rain_1h'] = res["rain"]["1h"] 
    if is_json_key_present(res, 'rain', '3h'):
        dict['rain_3h'] = res["rain"]["3h"]
    return dict

def get_weight(elevation):
    mean = 569
    std_dev = 53
    x = np.linspace(mean - 3*std_dev, mean + 3*std_dev, 1000)
    y = norm.pdf(x, mean, std_dev)
    weight = norm.pdf(elevation, mean, std_dev)
    # print(weight)
    # plt.plot(x, y, label='Normal Distribution')
    # plt.title(f'Normal Distribution with mean={mean} and std_dev={std_dev}')
    # plt.scatter([elevation], [weight], color='red', label=f'{weight}')
    # plt.xlabel('X-axis')
    # plt.ylabel('Probability Density Function (PDF)')
    # plt.legend()
    # plt.grid(True)
    # plt.show()
    return 1 + weight * 100

def avalanche_alarm(level, rainfall, elevation):
    dayvalue = get_weight(elevation) * sum(rainfall) # min : 441, max : 696
    timevalue = get_weight(elevation) * rainfall[-1]
    print(timevalue, dayvalue)
    if (level <= 2) and ((timevalue >= 30) or (dayvalue >= 150)):
        return 1
    if (level <= 2) and ((timevalue >= 20) or (dayvalue >= 80)):
        return 2
    return 3

def load_wamis_sim(): #시뮬레이션 wamis 정보 로드
    #1. 시간설정
    sim_dict = {} #key: YYmmddhh 형식, value: [rf, wl, iqty, tdqty]
    #강수량(rf)
    rf_list =[]
    rf_list.append(wamis("20230713", 2,2))
    rf_list.append(wamis("20230714", 2,2))
    rf_list.append(wamis("20230715", 2,2))
    for i in range(0,3):
        for j in rf_list[i]:
            for k in j['list']:
                sim_dict[k['ymdh']] = []
                sim_dict[k['ymdh']].append(float(k['rf']))
    #수위(wl)
    wl_list = []
    wl_list.append(wamis("20230714", 0,0))
    wl_list.append(wamis("20230715", 0,0))
    for i in range(0,2):
        for j in wl_list[i]:
            for k in j['list']:
                sim_dict[k['ymdh']].append(float(k['wl']))     
        
    #댐수문 - iqty(유입량), tdqty(방류량)
    dam_list=[]
    dam_list.append(wamis("20230714", 1,0))
    dam_list.append(wamis("20230715", 1,0))
    for i in range(0,2):
        for j in dam_list[i]:
            for k in j['list']:
                sim_dict[k['obsdh']].append(float(k['iqty']))
                sim_dict[k['obsdh']].append(float(k['tdqty']))
    # pp.pprint(sim_dict)
    
    return sim_dict

def load_wamis_cur(dt): #실시간 wamis 정보 로드
    
    wamis_dict ={}
    res = wamis(dt, 2,0)
    for i in res:
        for j in i['list']:
            wamis_dict[j['ymdh']] = []
            wamis_dict[j['ymdh']].append(float(j['rf']))

    res = wamis(dt, 0,0)
    for i in res:
        for j in i['list']:
            wamis_dict[j['ymdh']].append(float(j['wl']))
    res = wamis(dt, 1,0)
    for i in res:
        for j in i['list']:
            wamis_dict[j['obsdh']].append(float(j['iqty']))
            wamis_dict[j['obsdh']].append(float(j['tdqty']))
    
    return wamis_dict

def load_coor_sim(location):
    #위치 설정
    coor={}
    if location==0: #예천군 미호리 보문교
        coor = {'lat': 36.66154100010838, 'lon':128.5135448823666}
    elif location==1: #예천군 효자면 백석리
        coor = {'lat':36.799409186466946, 'lon':128.44686161183995}
    return coor

def find_minDistance(X):
    # file_name="/content/drive/MyDrive/total_andong_data.csv"
    csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/datas/', 'total_andong_data.csv')
    dis=pd.read_csv(csv_file_path)
    dis=dis.drop(['Unnamed: 0','Date','FlowRate'],axis=1)
    dis=dis.dropna()
    X_train_dam=dis.iloc[:int(len(dis)*0.9)]
    X_train_dam.loc[int(len(dis)*0.9)] = X

    minmax=MinMaxScaler()
    minmax.fit(X_train_dam)
    ip=minmax.transform(X_train_dam)

    input=ip[-1]
    input = input.reshape(1, 1,input.shape[0])
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/datas/', 'andong_dam_autoencoder.h5')
    dam_mod = load_model(model_path)
    # dam_mod=load_model('/content/drive/MyDrive/andong_dam_autoencoder.h5')

    input_prediction=dam_mod.predict(input)
    pre_dam=input_prediction.reshape(input_prediction.shape[0],input_prediction.shape[2])

    distances=[]
    # #클러스터링 과정
    centers = [[0.02535742, 0.02877325, 0.01759606, 0.0203388 ],[0.01727376, 0.69740885, 0.01330538, 0.09691893],
    [0.02331715, 0.4579334,  0.02241113, 0.06194941], [0.03298591, 0.10068072, 0.06891587, 0.06687615]]
    for i in range(len(centers)):
        distance=np.linalg.norm(pre_dam-centers[i])
        distances.append(distance)
    min_d=min(distances)
    # print(distances)
    if (min_d<0.285):
        return 3 #안전
    elif (min_d<0.748):
        return 1 #위험
    return 2 #주의

def generate_hourly_timestamps(start_timestamp):
    start_datetime = datetime.strptime(start_timestamp, '%Y%m%d%H')
    key = []
    for i in range(24):
        current_datetime = start_datetime - timedelta(hours=i)
        formatted_timestamp = current_datetime.strftime('%Y%m%d%H')
        key.append(formatted_timestamp)
    key.reverse()
    # 테스트
    #print(generate_hourly_timestamps('2023071910'))
    return key

# Create your views here.
def cover(request):
    return render(request, 'cover.html')

def menu1_home(request):
    menu = 1
    #위치 새로고침 버튼 클릭시 API 호출, 주소 계산
    if request.method == 'POST': #버튼 submit
        ymdh = request.POST.get('sim_btn') #시뮬레이션 날짜
        location = request.POST.get('sim_loc') #시뮬레이션 위치

        if ymdh==None or location == None: #일반 새로고침
            issim = 0
            dt = datetime.today()#오늘 날짜 호출
            dt_ymd = dt.strftime("%Y%m%d")
            dt_ymdh = dt.strftime("%Y%m%d%H")
            lat, lon = get_current_location()
            coor = {'lat':lat, 'lon':lon}

            wamis_dict = load_wamis_cur(dt_ymd)
            print('wamis - loaded by API')
            print('info - loaded by refresh button')
        else: #시뮬레이션
            issim = 1 #시뮬레이션 중 인지 체크
            dt_ymdh = ymdh
            dt_ymd = dt_ymdh[:-2] ##hh제거
            try:
                wamis_dict = request.session[dt_ymd]
                print('wamis - loaded by session')
            except:
                wamis_dict = load_wamis_sim()
                print('wamis - loaded by API')

            coor = load_coor_sim(int(location))
            lat = coor['lat']
            lon = coor['lon']
            wamis_rf = 0 #실시간 정보는 openweather에서 가져오므로 안 씀, 초기화만 
            print('info - loaded by simulation button')

        address = latalt_to_addr(lat, lon)
        alt = get_altitude(lat, lon)
        ow_dict = openweather(lat, lon)

        #재난 위험 레벨 측정
        #wamis_dict['날짜(년월일시)'] = [강수량, 수위, 유입량, 방류량]
        try:
            wamis_rf = wamis_dict[dt_ymdh][0]
            flood_level = find_minDistance(list(wamis_dict[dt_ymdh]))
        except:
            #24시인 것 0으로 번경
            if dt_ymdh[8:] == '24':
                dt_ymdh = dt_ymdh[:-2] + '00'
            dt_datetime = datetime.strptime(dt_ymdh, '%Y%m%d%H')
            dt_1hr_bef = (dt_datetime - timedelta(hours=1)).strftime('%Y%m%d%H')
            wamis_rf = wamis_dict[dt_1hr_bef][0]
            flood_level = find_minDistance(list(wamis_dict[dt_1hr_bef]))
        #rf강수량만 선별
        date_list = list(wamis_dict.keys())
        wl_list=[]
        for i in range(len(date_list)):
            if dt_ymd in date_list[i]:
                wl_list.append(wamis_dict[date_list[i]][0])
        aval_level = avalanche_alarm(flood_level,wl_list ,alt)

        #세션 저장 -> API 재호출 방지
        request.session['address'] = address
        request.session['coor'] = coor
        request.session['alt'] = alt
        request.session['ow_dict'] = ow_dict
        request.session['dt_ymdh'] = dt_ymdh
        request.session[dt_ymd] = wamis_dict
        request.session['fl'] = flood_level
        request.session['av'] = aval_level
        request.session['issim'] = issim
        request.session['wamis_rf'] = wamis_rf
    else:
        address = request.session.get('address',"정보 새로고침을 해주세요.")
        coor = request.session.get('coor',None)
        alt = request.session.get('alt',None)
        ow_dict = request.session.get('ow_dict',None)
        dt_ymdh = request.session.get('dt_ymdh',None)
        flood_level = request.session.get('fl',-1)
        aval_level = request.session.get('av', -1)
        issim = request.session.get('issim', 0)
        wamis_rf = request.session.get('wamis_rf', 0)
        print('info - loaded by session')
        
    print('현재 위치 - {}'.format(address))
    print('현재 고도 - {}'.format(alt))
    print('현재 기온 정보 - {}'.format(ow_dict))
    # pp.pprint('wamis 정보 - {}'.format(wamis_dict))
    print("호우 등급: {}, 산사태 등급: {}".format(flood_level, aval_level))
    #1 : 위험 | 2: 주의 | 3: 안전
    if dt_ymdh == None:
        today = None
    else:
        #24시인 것 0으로 번경
        if dt_ymdh[8:] == '24':
            dt_ymdh = dt_ymdh[:-2] + '00'
        today_datetime= datetime.strptime(dt_ymdh, '%Y%m%d%H')
        # print(today_datetime)
        today = today_datetime.strftime('%Y년%m월%d일 %H시')
        print(today)

    return render(request, 'menu1/home.html',{'issim':issim, 'rf':wamis_rf, 'fl':flood_level, 'av':aval_level, 'api_key':youtube_api_key1, 'dt':today, 'menu':menu,'address':address, 'coor':coor, 'ow_dict':ow_dict})

def menu2_home(request):
    menu=2
    return render(request, 'menu2/home.html',{'menu':menu})

def menu3_home(request):
    menu=3
    if request.method == 'POST':
        print("글쓰기 요청")
        author = request.POST['author']
        title = request.POST['title']
        content = request.POST['content']
        print('작성자:{}, 제목:{}, 내용:{}'.format(author, title, content))
        board = Board(author=author, title=title, content=content)
        board.save()
        return redirect('menu3_home')
    else:
        boards = Board.objects.all()
        return render(request, 'menu3/home.html', {'menu':menu, 'boards':boards})
    
def menu3_post(request, id):
    menu=3
    try:
        board=Board.objects.get(pk=id)
    except Board.DoesNotExist:
        raise Http404("게시글이 더 이상 존재하지 않습니다.")
    return render(request, 'menu3/post.html', {'menu':menu,  'board':board})
