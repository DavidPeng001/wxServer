# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session

import urllib2
import json
import base64
from api.models import User, Room
import api.robot as robot

@api_view(['POST','GET'])
def keyword_search_api(request):
	if request.method == 'POST':
		data = json.loads(request.body)[u'keyword']  # unicode
		if data.strip() == '':
			return Response(status = status.HTTP_400_BAD_REQUEST)
		data = urllib2.quote(data.encode('utf-8'))
		page=  json.loads(request.body)[u'page']
		# request.data should be json obj TODO: exceotion handle
	elif request.method == 'GET':
		data = request.GET.get('keyword', '')       # URL
		if data.strip() == '':
			return Response(status = status.HTTP_400_BAD_REQUEST)
		page = request.GET.get('page', 0)
	else:
		return Response(status = status.HTTP_405_METHOD_NOT_ALLOWED)
	return JsonResponse(robot.keyword_search(data, int(page)), safe=False)

@api_view(['POST'])
def info_search_api(request):
	if request.method == 'POST':
		href = json.loads(request.body)[u'href']  # unicode
		if href.strip() == '':
			return Response(status = status.HTTP_400_BAD_REQUEST)
		return JsonResponse(robot.search_info(href), safe=False)

def connection_test(request):
	return HttpResponse('Welcome! Connection is right.')

@api_view(['POST'])
def login(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		personnelno = data[u'id']
		password_lib = data[u'passwd_lib']
		password_space = data[u'passwd_space']
		if not User.objects.filter(id=personnelno).exists():
			status = robot.register(personnelno, password_lib, password_space)
			if status == 0:
				s = SessionStore()
				s['id'] = personnelno
				s.create()
				response = JsonResponse({'status': 'register_success'}, safe=False)
				response.set_cookie('JSESSIONID', s.session_key)
				return response
			else:
				return JsonResponse({'status': 'wrong'}, safe=False)
		else:
			if User.objects.get(id=personnelno).password_lib == password_lib:
				s = SessionStore()
				s['id'] = personnelno
				# delete previous session
				# print s.encode({'id': personnelno})
				Session.objects.filter(session_data = s.encode({'id': personnelno})).delete()
				s.save()
				response = JsonResponse({'status': 'ok'}, safe=False)
				response.set_cookie('JSESSIONID', s.session_key)
				return response
			else:
				return JsonResponse({'status': 'wrong'}, safe=False)
			# TODO: session 过期设置

@api_view(['GET'])
def quick_login(request):
	if request.method == 'GET':
		try:
			s = SessionStore(session_key=request.COOKIES['JSESSIONID'])
			return JsonResponse({'id': s['id']}, safe=False)
		except KeyError:
			return JsonResponse({'id': u'wrong'}, safe=False)


@api_view(['POST'])
def room_search(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		start, end = data['start'], data['end']
		rooms = Room.objects.filter(date=data['date'])
		# regenerate room table
		table = dict()
		for room in rooms:
			base_bin = bin(room.availability)[2:]
			room_dict = {room.room: list((15 - len(base_bin)) * '0' + base_bin)}
			table.update(room_dict)
		# sort by its available time length
		results = []
		for room_name, room_list in table.items():
			if max(room_list[start - 8: end - 8]) == 0:
				continue
			hour_length = []  # 记录每一时刻之前(包括该时刻)的连续可用时长
			for hour in room_list[start - 8: end - 8]:
				if hour == 1:
					if hour_length != []:
						hour_length.append(hour_length[-1] + 1)
					else:  # first of loop
						hour_length.append(1)
				else:
					hour_length.append(0)
			result = dict()
			result['room'] = room_name
			result['end'] = start + hour_length.index(max(hour_length)) + 1
			result['length'] = max(hour_length)
			result['start'] = result['end'] - result['length']
			results.append(result)
		return  JsonResponse(sorted(results, key=lambda x: x.pop('length'), reverse=True), safe=False)

@api_view(['POST'])
def room_booking(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		s = SessionStore(session_key=request.COOKIES['JSESSIONID'])
		user = User.objects.get(id=s['id'])
		status = robot.room_booking(data['date'], data['room'], data['start'], data['end'], user.sessionid_space)
		if status == 2:  # sessionid_space expired
			if robot.update_sessionid_space(user.id,user.password_space) == 0:
				status = robot.room_booking(data['date'], data['room'], data['start'], data['end'],user.sessionid_space)
			else:
				status = 3
		return JsonResponse({'status': status}, safe=False)




