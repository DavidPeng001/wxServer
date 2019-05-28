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
			status_space = robot.space_login(personnelno, password_space)
			status_lib = robot.pre_login(personnelno, password_lib)
			if status_lib["status"] == 0 and status_space["status"] == 0:
				s = SessionStore()
				s['data'] = {'id': personnelno, 'passwd_lib': password_lib, 'passwd_space': password_space, 'data_lib':status_lib["session_data"][0],
							 'sessionid_lib': status_lib["session_data"][1], 'sessionid_space': status_space["session_data"] }
				s.create()
				response = JsonResponse({'status': 2, 'captcha': status_lib["response_data"]}, safe=False) # captcha needed
				response.set_cookie('JSESSIONID', s.session_key)
				return response
			else:
				return JsonResponse({'status': 1}, safe=False)
		else:
			if User.objects.get(id=personnelno).password_lib == password_lib:
				s = SessionStore()
				s['id'] = personnelno
				# delete previous session
				Session.objects.filter(session_data = s.encode({'id': personnelno})).delete()
				s.save()
				response = JsonResponse({'status': 0}, safe=False)
				response.set_cookie('JSESSIONID', s.session_key)
				return response
			else:
				return JsonResponse({'status': 1}, safe=False) # wrong password / username
			# TODO: session 过期设置

@api_view(['GET'])
def update_captcha(request):
	if request.method == 'GET':
		s = SessionStore(session_key=request.COOKIES['JSESSIONID'])
		session_data = s["data"]
		status = robot.pre_login(session_data[0], session_data[1])
		if status["status"] == 0:
			session_data["data_lib"] = status["session_data"][0]
			session_data["sessionid_lib"] = status["session_data"][1]
			# no need to check space password correction, because it already checked.
			s = SessionStore()
			s['data'] = session_data
			s.create()
			response = JsonResponse({'status': 0, 'captcha': status["response_data"]}, safe=False)
			response.set_cookie('JSESSIONID', s.session_key)
			return response
		else:
			return JsonResponse({'status': 1}, safe=False) # something wrong, back and login again
		
@api_view(['POST'])
def login_with_captcha(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		captcha = data[u'captcha']
		s = SessionStore(session_key=request.COOKIES['JSESSIONID']) # TODO: check is None
		session_data = s["data"]
		status = robot.lib_login(session_data, captcha)
		if status["status"] == 0:
			s = SessionStore()
			s['id'] = session_data['id']
			s.create()
			response = JsonResponse({'status': 0}, safe=False)
			response.set_cookie('JSESSIONID', s.session_key)
			return response
		else:
			return JsonResponse({'status': status}, safe=False)



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
			room_list = list((15 - len(base_bin)) * '0' + base_bin)
			room_dict = {room.room: map(int, room_list)}
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
		if status["status"] == 2:  # sessionid_space expired
			status_space = robot.space_login(user.id, user.password_space)
			if status_space["status"] == 0:
				user.sessionid_space = status_space["session_data"]
				user.save()
				status = robot.room_booking(data['date'], data['room'], data['start'], data['end'], status_space["session_data"])
			else:
				status["status"] = 3  # password wrong

		return JsonResponse({'status': status}, safe=False)

@api_view(['GET'])
def book_renew_search(request):
	if request.method == 'GET':
		# data = json.loads(request.body)
		s = SessionStore(session_key=request.COOKIES['JSESSIONID'])
		user = User.objects.get(id=s['id'])
		status = robot.book_renew_search(user.sessionid_lib)
		if status["status"] == 0:
			return JsonResponse({'status': 0, 'table': status['table']}, safe=False)
		elif status["status"] == 1:  # sessionid_space expired
			status_lib = robot.pre_login(user.id, user.password_space)
			if status_lib["status"] == 0:
				s = SessionStore()
				s['data'] = {'id': user.id, 'passwd_lib': user.password_lib, 'passwd_space': user.password_space, 'data_lib':status_lib["session_data"][0],
							 'sessionid_lib': status_lib["session_data"][1], 'sessionid_space': user.sessionid_space }
				s.create()  # additional data
				response = JsonResponse({'status': 1, 'captcha': status["response_data"]}, safe=False)
				response.set_cookie('JSESSIONID', s.session_key)
				return response
		else:
			return JsonResponse({'status': -1}, safe=False)

@api_view(['POST'])
def book_renew_search_with_captcha(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		captcha = data[u'captcha']
		s = SessionStore(session_key=request.COOKIES['JSESSIONID']) # TODO: check is None
		session_data = s["data"]
		status_login = robot.lib_login(session_data, captcha)
		if status_login["status"] == 0:
			s = SessionStore()
			s['id'] = session_data['id']
			s.create()
			user = User.objects.get(id=session_data['id'])
			status = robot.book_renew_search(user.sessionid_lib)
			if status["status"] == 0:
				response =  JsonResponse({'status': 0}, safe=False) # 0 for success
				response.set_cookie('JSESSIONID', s.session_key)
				return  response
			elif status["status"] == 1:
				return JsonResponse({'status': 1}, safe=False) # 1 for cookie expired
			else:
				return JsonResponse({'status': -1}, safe=False) # 2 for web error
		else:
			return JsonResponse({'status': status_login["status"]}, safe=False)
			# 101 for captcha wrong
			# 102 for username or password wrong
			# 103 for unkonown
			# TODO: delete record.

@api_view(['POST'])
def book_renew(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		s = SessionStore(session_key=request.COOKIES['JSESSIONID'])
		user = User.objects.get(id=s['id'])
		status = robot.book_renew(user.sessionid_lib, data['bookid'])
		if status["status"] == 0:
			return JsonResponse({'status': 0}, safe=False)
		elif status["status"] == 1:  # sessionid expired
			status_lib = robot.pre_login(user.id, user.password_space)
			if status_lib["status"] == 0:
				s = SessionStore()
				s['data'] = {'id': user.id, 'passwd_lib': user.password_lib, 'passwd_space': user.password_space, 'data_lib':status_lib["session_data"][0],
							 'sessionid_lib': status_lib["session_data"][1], 'sessionid_space': user.sessionid_space, 'book_id': data['bookid'] }
				s.create()                                                                                                           # additional data
				response = JsonResponse({'status': 1, 'captcha': status["response_data"]}, safe=False)
				response.set_cookie('JSESSIONID', s.session_key)
				return response
		else:
			return JsonResponse({'status': status}, safe=False) # web error


@api_view(['POST'])
def book_renew_with_captcha(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		captcha = data[u'captcha']
		s = SessionStore(session_key=request.COOKIES['JSESSIONID']) # TODO: check is None
		session_data = s["data"]
		status_login = robot.lib_login(session_data['id'], captcha)
		if status_login["status"] == 0:
			s = SessionStore()
			s['id'] = session_data[0]
			s.create()
			user = User.objects.get(id=session_data['id'])
			status = robot.book_renew(user.sessionid_lib, session_data['book_id']) # additional data: book id
			if status["status"] == 0:
				response =  JsonResponse({'status': 0}, safe=False)
				response.set_cookie('JSESSIONID', s.session_key)
				return  response
			else:
				return JsonResponse({'status': status}, safe=False)
		else:
			return JsonResponse({'status': status_login["status"]}, safe=False) # password wrong, logout, TODO: delete record.
			# interface info is same as function book_renew_search_with_captcha(request)
