# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.contrib.sessions.backends.db import SessionStore
import urllib2
import json
import base64
from api.models import User
import api.robot as robot

@api_view(['POST','GET'])
def keyword_search_api(request):
	if request.method == 'POST':
		data = json.loads(request.body)[u'keyword']  # unicode
		if data.strip() == '':
			return Response(status = status.HTTP_400_BAD_REQUEST)
		data = urllib2.quote(data.encode('utf-8'))
		page=  json.loads(request.body)[u'page']
		# request.data should be json obj
	elif request.method == 'GET':
		data = request.GET.get('keyword', '')       # URL
		if data.strip() == '':
			return Response(status = status.HTTP_400_BAD_REQUEST)
		page = request.GET.get('page', 0)
	else:
		return Response(status = status.HTTP_405_METHOD_NOT_ALLOWED)
	return JsonResponse(robot.keyword_search(data, int(page)), safe=False)



def connection_test(request):
	return HttpResponse('Welcome! Connection is right.')

@api_view(['POST'])
def login(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		personnelno = data[u'id']
		password_lib = base64.b64decode(data[u'passwd_lib'])
		password_space = base64.b64decode(data[u'passwd_space'])
		if User.objects.filter(id=personnelno) != []:
			robot.register(personnelno, password_lib, password_space)
			s = SessionStore()
			s['id'] = personnelno
			s.create()
			response = JsonResponse({'status': 'register_success'}, safe=False)
			response.set_cookie('JSESSIONID', s.session_key)
			return response
		else:
			if User.objects.get(id=personnelno).password_lib == password_lib:
				return JsonResponse({'status': 'ok'}, safe=False)
			else:
				return JsonResponse({'status': 'wrong'}, safe=False)


@api_view(['GET'])
def quick_login(request):
	if request.method == 'GET':
		s = SessionStore(session_key=request.COOKIES['JSESSIONID'])
		return JsonResponse({'id': s['id']}, safe=False)


