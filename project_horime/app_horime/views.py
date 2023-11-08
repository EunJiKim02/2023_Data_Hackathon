from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
import os
import requests
from geopy.geocoders import Nominatim

#http로 실행했을 때 오류 방지
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

#Youtube Geolocation API를 활용하여 로드
def get_current_location():
    # YOUTUBE API 키
    API_KEY = ['AIzaSyCcis4wzheGUE8j9hRQ9xp43w7LREedD6M',
            'AIzaSyCybUkLvjkdaWFgdc7GtVdnn-vgal0g0mg']
    # 현재 위치 요청
    try:
        url = "https://www.googleapis.com/geolocation/v1/geolocate?key={}".format(API_KEY[0])
    except: #API 할당량 다차면 다른 키 가져오기
        url = "https://www.googleapis.com/geolocation/v1/geolocate?key={}".format(API_KEY[1])
    response = requests.post(url)

    # 요청이 성공하면 응답을 처리
    if response.status_code == 200:
        # 위도와 경도를 추출
        latitude = response.json()["location"]["lat"]
        longitude = response.json()["location"]["lng"]
        return latitude, longitude
    else:
        # 요청이 실패하면 오류를 출력
        print("요청실패 코드{}오류".format(response.status_code))
        return None, None

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

# Create your views here.
def cover(request):
    return render(request, 'cover.html')

def menu1_home(request):
    menu=1
    #위치 새로고침 버튼 클릭시 API 호출, 주소 계산
    if request.method == 'POST':
        lat, lon = get_current_location()
        address = latalt_to_addr(lat, lon)
        request.session['address'] = address #세션 저장 -> API 재호출 방지
        print('location - loaded by refresh button')
    elif request.session.get('address') == None:
        address = "위치를 불러와 주세요."
        print('location - session not loaded')
    else:
        address = request.session.get('address')
        print('location - loaded by session')
        
    print('현재 위치 - {}'.format(address))
    return render(request, 'menu1/home.html',{'menu':menu,'address':address})

def menu2_home(request):
    menu=2
    return render(request, 'menu2/home.html',{'menu':menu})

def menu3_home(request):
    menu=3
    return render(request, 'menu3/home.html',{'menu':menu})

def menu4_home(request):
    menu=4
    if request.method == 'POST':
        print("글쓰기 요청")
        author = request.POST['author']
        title = request.POST['title']
        content = request.POST['content']
        print('작성자:{}, 제목:{}, 내용:{}'.format(author, title, content))
        board = Board(author=author, title=title, content=content)
        board.save()
        return redirect('menu4_home')
    else:
        boards = Board.objects.all()
        return render(request, 'menu4/home.html', {'menu':menu, 'boards':boards})
