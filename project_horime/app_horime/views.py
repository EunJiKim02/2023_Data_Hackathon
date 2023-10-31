from django.shortcuts import render
import os

#http로 실행했을 때 오류 방지
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Create your views here.
def cover(request):
    return render(request, 'cover.html')

def home(request):
    return render(request, 'home.html')
