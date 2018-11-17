# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render

import urllib2
from urllib2 import HTTPError,URLError
from lxml import etree
import json

@api_view(['POST'])
def keyword_search_api(requset):
	return Response(toJSON(keyword_search(requset.data)), status=200 )
	# request.data should be unicode
	# TODO: try to use url to transmit keyword

def keyword_search(keyword):
	url = "http://opac.jnu.edu.cn/search*chx/?searchtype=X&SORT=D&searcharg=" + urllib2.quote(keyword.encode('utf-8')) + "&searchscope=1&submit.x=0&submit.y=0"
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
	print 'Connection Established \n *****'
	html = html.decode('utf8')
	selector = etree.HTML(html)

	books = []
	for index in range(4, 16):
		contents = selector.xpath("//table[@class='browseScreen']/tr[2]/td/table[1]/tr[" + str(index) + "]//*/text()")
		book_info = {}
		if len(contents) > 8:
			book_info['libinfo'] = []
		i = 0
		for content in contents:
			if content.strip() != '' and content.strip() != '\n':
				if i == 1:
					book_info['name'] = content
				elif i == 2:
					content = "".join(content.split(u'\xa0')) [1:]
					auth = content[content.find('/')+1: content.find('\n')]
					# remove \xa0 and \n on the front, then get part between / and \n
					book_info['auth'] = "".join(auth.split()) [:-1].split(u'，')
					# remove all space and 著 at last, then get a list
					#TODO: 某些记录没有作者字段，请做鲁棒性检查
					publish = content[content.find('\n')+1: content.rfind('\n')]
					book_info['publish'] = publish[publish.find(':')+1 if(publish.find(':')!=-1) else 0: publish.rfind(',')]
				elif i == 9 or i == 13 or i == 17:
					lib_info = {}
					lib_info['location'] = "".join(content.split())
				elif i == 10 or i == 14 or i == 18:
					lib_info['index'] = "".join(content.split(u'\xa0'))
				elif i == 12 or i == 16 or i == 20:
					lib_info['status'] = "".join(content.split(u'\xa0')).strip()
					book_info['libinfo'].append(lib_info)
				i += 1
		books.append(book_info)
	return books


def toJSON(books):
	string = json.dumps(books)
	return string