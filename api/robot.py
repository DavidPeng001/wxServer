# -*- coding: utf-8 -*-
import urllib2
from urllib2 import HTTPError,URLError
from lxml import etree
import urllib
import requests
import json
from api.models import User


def keyword_search(keyword, page):  # keyword: str urlencode from utf-8  page: int
	seq = page * 12 + 1
	url = "https://opac.jnu.edu.cn/search~S1*chx?/X" + keyword + "&searchscope=1&SORT=D/X" + keyword + \
	      "&searchscope=1&SORT=D&SUBKEY=/" + str(seq) + "%2C499%2C499%2CB/browse"
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
	}
	data = None
	html = None
	try:
		request = urllib2.Request(url, data, headers)
		html = urllib2.urlopen(request).read()
	except (HTTPError, URLError):
		print "Couldn't connect to opac.jnu.edu.cn."
		exit()
	# TODO: if exception return something
	# TODO: if html
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
				auth = content[content.find('/') + 1: content.find('\n')]
				# remove \xa0 and \n on the front, then get part between / and \n
				book_info['auth'] = "".join(auth.split())[:-1].split(u'，')
				# remove all space and 著 at last, then get a list
				publish = content[content.find('\n') + 1: content.rfind('\n')]
				book_info['publish'] = publish[
				                       publish.find(':') + 1 if (publish.find(':') != -1) else 0: publish.rfind(',')]
				# print book_info['auth']
				# print book_info['publish']
				break
		# FIXME: 作者字段大部分以‘著’结束，但少数以‘编著’结束，或以‘\n’结束
		book_info['libinfo'] = []
		try:
			for i in range(1, 4):
				lib_info = {}
				location = selector.xpath(root_path + "//tr[@class='bibItemsEntry'][$seq]/td[1]/text()", seq=i)
				if len(location) == 2:  # when location field is a hyperlink length of location list is 2
					location = selector.xpath(root_path + "//tr[@class='bibItemsEntry'][$seq]/td[1]/*/text()", seq=i)[0]
				else:
					location = location[0]
				index = selector.xpath(root_path + "//tr[@class='bibItemsEntry'][$seq]/td[2]//*/text()", seq=i)[0]
				status = selector.xpath(root_path + "//tr[@class='bibItemsEntry'][$seq]/td[4]/text()", seq=i)[0]
				lib_info['location'] = "".join(location.split(u'\xa0')).strip()
				lib_info['index'] = index
				lib_info['status'] = "".join(status.split(u'\xa0')).strip()
				book_info['libinfo'].append(lib_info)
		except IndexError:
			pass
		books.append(book_info)
	return books


def register(personnelno, passwd_lib, passwd_space):
	url_lib = "https://libsouth.jnu.edu.cn/auth/login.json"
	url_space = "https://libsouthic.jnu.edu.cn/login.userlogin"
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
		"Content-Type": "application/x-www-form-urlencoded"
		# 表示浏览器提交web表单时，表单数据会按照name1=value1&name2=value2键值对形式进行编码。
	}
	data_lib = {
		"personnelno": personnelno,
		"password": passwd_lib,
	}
	data_space = {
		"t:formdata": "YO0mInLsxupSFzTGH68d4QXjK7k=:H4sIAAAAAAAAAJWQPUoEQRCFywFlYWURwcBc014DN9HERRCEQYTBWHp6yrGlp7vtqnHWxMhLmHgCMdITbGDmHTyAiYGRgfODsLAimBUfj3of7+EdFqsBLMcu13anJAw6owAjF3IhvVTnKFh6JA7XI6FcQKNTkUpCMU5rKBUfaDTZRoJc+s2Taf9t7eUrgoUY+spZDs4cyQIZVuMLeSWHRtp8mHDQNt+deIalrvEXg/F/DY6DU0iUlGmhibSz08ds++zz/jUCmPhqBQZdg5dElQsZXcINAEPvB8xHmsTMOtS85tpt70835QrvLFom0crwvNpd8rH+/HS7H0EUQ08ZXacP27pmODRY1KAZrkXNUL2u/HRr5vwGvfD11LwBAAA=",
		"t:submit": "[\"submit_0\",\"submit_0\"]",
		"userid": personnelno,
		"password": passwd_space,
		"submit_0": "登录",
	}
	cookie_lib = ''
	cookie_space = ''

	response_lib = requests.post(url_lib, data=urllib.urlencode(data_lib), headers=headers)
	html = response_lib.content.decode('utf8')
	json_dict = json.loads(html)
	if json_dict[u'errors'] != {}:
		return 1
	for k, v in response_lib.cookies.items():
		if k == 'JSESSIONID':
			cookie_lib = v

	response_space = requests.post(url_space, data=urllib.urlencode(data_space), headers=headers)
	html = response_space.content.decode('utf8')
	selector = etree.HTML(html)
	error_test = selector.xpath("//div[@class='t-error']")
	if error_test != []:
		return 1
	for k, v in response_space.history[0].cookies.items():
		if k == 'JSESSIONID':
			cookie_space = v

	user = User(id=personnelno, password_lib=passwd_lib, password_space=passwd_space, sessionid_lib=cookie_lib, sessionid_space=cookie_space)
	user.save()

	return 0

	# 0 -> success  1 -> password wrong  -1 -> error




