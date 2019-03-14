# -*- coding: utf-8 -*-
import urllib2
from urllib2 import HTTPError,URLError
from lxml import etree
import urllib
import requests
import json
from api.models import User


def keyword_search(keyword,page):
	seq = page*10
	url = "https://opac.jnu.edu.cn/opac/search?searchModel=include&field=title&q=%s&pager.offset=%d" % (keyword, seq)
	headers = {
	"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
	}

	try:
		response = requests.get(url, headers=headers)
		html = response.content
	except (HTTPError,URLError):
		print "Couldn't connect to opac.jnu.edu.cn."
		exit()
	print 'Connection Established \n *****'
	# html = html.decode('utf8')
	tree = etree.HTML(html)

	books = []
	for index in range(1, 11):
		root_path = "//div[@class='jp-searchList']/ul/li[%d]" % index
		book_info = {}
		book_info['title'] = tree.xpath(root_path + "/h2/a/text()")[0]
		book_info['auth'] = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='creator']//a/text()")[0].strip()
		book_info['publisher'] = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='publisher']/text()")[-1].strip()
		book_info['topic'] = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='subject']/text()")[-1].strip()
		books.append(book_info)
	return  books



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




