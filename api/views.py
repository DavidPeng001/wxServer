# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.http import HttpResponse,JsonResponse

import urllib2
from urllib2 import HTTPError,URLError
from lxml import etree
import json

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
	return JsonResponse(keyword_search(data, int(page)), safe=False)


def keyword_search(keyword,page):  # keyword: str urlencode from utf-8  page: int
	seq = page*12 + 1
	url = "https://opac.jnu.edu.cn/search~S1*chx?/X" + keyword + "&searchscope=1&SORT=D/X" + keyword +\
	      "&searchscope=1&SORT=D&SUBKEY=/" + str(seq) + "%2C499%2C499%2CB/browse"
	headers = {
	"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
	}
	data = None

	try:
		request = urllib2.Request(url, data, headers)
		html = urllib2.urlopen(request).read()
	except (HTTPError,URLError):
		print "Couldn't connect to opac.jnu.edu.cn."
		exit()
		# TODO: if exception return something
	html = html.decode('utf8')
	selector = etree.HTML(html)

	books = []
	for index in range(4, 16):
		root_path = "//table[@class='browseScreen']/tr[2]/td/table[1]/tr[" + str(index) + "]"
		book_info = {}
		book_info['name'] = selector.xpath(root_path + "//span[@class='briefcitTitle']//*/text()")[0]
		contents = selector.xpath(root_path + "//td[@class='briefcitDetail']/text()")
		for content in contents:
			if content.strip() != '' and content.strip() != '\n':
				content = "".join(content.split(u'\xa0'))[1:]
				auth = content[content.find('/')+1: content.find('\n')]
				# remove \xa0 and \n on the front, then get part between / and \n
				book_info['auth'] = "".join(auth.split()) [:-1].split(u'，')
				# remove all space and 著 at last, then get a list
				publish = content[content.find('\n') + 1: content.rfind('\n')]
				book_info['publish'] = publish[publish.find(':')+1 if(publish.find(':')!=-1) else 0: publish.rfind(',')]
				# print book_info['auth']
				# print book_info['publish']
				break
				# FIXME: 作者字段大部分以‘著’结束，但少数以‘编著’结束，或以‘\n’结束
		book_info['libinfo'] = []
		try:
			for i in range(1, 4):
				lib_info = {}
				location = selector.xpath(root_path + "//tr[@class='bibItemsEntry'][$seq]/td[1]/text()", seq=i)
				if len(location) == 2:    # when location field is a hyperlink length of location list is 2
					location = selector.xpath(root_path + "//tr[@class='bibItemsEntry'][$seq]/td[1]/*/text()", seq=i)[0]
				else:
					location = location[0]
				index = selector.xpath(root_path + "//tr[@class='bibItemsEntry'][$seq]/td[2]//*/text()", seq=i)[0]
				status = selector.xpath(root_path + "//tr[@class='bibItemsEntry'][$seq]/td[4]/text()", seq=i)[0]
				lib_info['location'] = "".join(location.split(u'\xa0')).strip()
				lib_info['index'] = index
				lib_info['status'] =  "".join(status.split(u'\xa0')).strip()
				book_info['libinfo'].append(lib_info)
		except IndexError:
			pass
		books.append(book_info)
	return books

def connection_test(request):
	return HttpResponse('Welcome! Connection is right.')