# -*- coding: utf-8 -*-
import urllib2
from urllib2 import HTTPError,URLError
from urllib import quote
from lxml import etree
from requests.cookies import RequestsCookieJar
import urllib
import requests
import json
import datetime
import random
import base64
from api.models import User


def keyword_search(keyword,page):
	seq = page*10
	url = "https://opac.jnu.edu.cn/opac/search?searchModel=contain&field=title&q=%s&pager.offset=%d" % (keyword, seq)
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
		title = tree.xpath(root_path + "/h2/a/text()")
		if title == []:
			break
		book_info['title'] = title[0]
		book_info['auth'] = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='creator']//a/text()")[0].strip()
		book_info['publisher'] = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='publisher']/text()")[-1].strip()
		topic_list = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='subject']/text()")
		if topic_list == []:
			book_info['topic'] = ""
		else:
			topics = topic_list[-1].split('\t')
			topic_list = []
			for topic in topics:
				topic = topic.replace(u'\r\n', u'').strip(u'\xa0')
				if topic != '':
					topic_list.append(topic)
					topic_list = list(set(topic_list))
			book_info['topic'] = " ".join(topic_list)
		book_info['href'] = tree.xpath(root_path + "/h2/a/@href")[0].replace('/opac/book/', '').strip('\r\n')
		book_info['langrage'] = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='libraryCount']/span/text()")[-1].strip('\r\n')
		book_info['index'] = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='call_number']/text()")[-1].strip()
		isbn = tree.xpath(root_path + "/div[@class='jp-booksInfo']/p[@class='isbn']/text()")
		if isbn != []:
			book_info['isbn'] = isbn[-1].strip()
		books.append(book_info)
	print books
	return  books

def space_login(personnelno, passwd_space): # TODO: not 200 return -1
	url_space = "https://libsouthic.jnu.edu.cn/login.userlogin"
	data_space = {
		"t:formdata": "YO0mInLsxupSFzTGH68d4QXjK7k=:H4sIAAAAAAAAAJWQPUoEQRCFywFlYWURwcBc014DN9HERRCEQYTBWHp6yrGlp7vtqnHWxMhLmHgCMdITbGDmHTyAiYGRgfODsLAimBUfj3of7+EdFqsBLMcu13anJAw6owAjF3IhvVTnKFh6JA7XI6FcQKNTkUpCMU5rKBUfaDTZRoJc+s2Taf9t7eUrgoUY+spZDs4cyQIZVuMLeSWHRtp8mHDQNt+deIalrvEXg/F/DY6DU0iUlGmhibSz08ds++zz/jUCmPhqBQZdg5dElQsZXcINAEPvB8xHmsTMOtS85tpt70835QrvLFom0crwvNpd8rH+/HS7H0EUQ08ZXacP27pmODRY1KAZrkXNUL2u/HRr5vwGvfD11LwBAAA=",
		"t:submit": "[\"submit_0\",\"submit_0\"]",
		"userid": personnelno,
		"password": passwd_space,
		"submit_0": "登录",
	}
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
		"Content-Type": "application/x-www-form-urlencoded"
		# 表示浏览器提交web表单时，表单数据会按照name1=value1&name2=value2键值对形式进行编码。
	}
	response_space = requests.post(url_space, data=urllib.urlencode(data_space), headers=headers)
	html = response_space.content.decode('utf8')
	selector = etree.HTML(html)
	error_test = selector.xpath("//div[@class='t-error']")
	if error_test != []:
		return {"status": 1}
	sessionid_space = response_space.history[0].cookies['JSESSIONID']
	return {"status": 0, "session_data": sessionid_space}


def pre_login(personnelno, passwd_lib):
	url_lib = "https://libcas.jnu.edu.cn/cas/login?service=http://opac.jnu.edu.cn/opac/search/simsearch"
	url_captcha = "https://libcas.jnu.edu.cn/cas/code/captcha.jpg" + str(random.uniform(0, 1))
	# FIXME: 当url_captcha不变，会生成相同验证码图片

	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
		"Content-Type": "application/x-www-form-urlencoded"
		# 表示浏览器提交web表单时，表单数据会按照name1=value1&name2=value2键值对形式进行编码。
	}
	response_lib = requests.get(url_lib, headers=headers)
	sessionid_lib = response_lib.cookies['JSESSIONID']
	tree = etree.HTML(response_lib.content.decode('utf8'))
	lt_token = tree.xpath("//input[@name='lt']/@value")[0]
	execution_token = tree.xpath("//input[@name='execution']/@value")[0]
	response_captcha = requests.get(url_captcha, headers=headers, cookies=response_lib.cookies)
	captcha_b64 = base64.b64encode(response_captcha.content)
	data_lib = {
		'username': personnelno,
		'password': passwd_lib,
		'captcha': "",
		'lt': lt_token,
		'execution': execution_token,
		'_eventId': 'submit'
	}
	return {"status": 0, "session_data": [data_lib, sessionid_lib] , "response_data": captcha_b64}

	# session_data = {
	# 				  'id': personnelno,
	# 				  'passwd_lib': password_lib,
	# 				  'passwd_spacep': password_space,
	#                 'data_lib':status_lib["session_data"][0],
	#                 'sessionid_lib': status_lib["session_data"][1],
	#                 'sessionid_space': status_space["session_data"]
	# 				}

def lib_login(session_data, captcha_text):
	url_lib = "https://libcas.jnu.edu.cn/cas/login?service=http://opac.jnu.edu.cn/opac/search/simsearch"
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
		"Content-Type": "application/x-www-form-urlencoded"
	}
	data_lib = session_data['data_lib']
	data_lib['captcha'] = captcha_text
	cookie_lib = RequestsCookieJar()
	cookie_lib.set('JSESSIONID', session_data['sessionid_lib'], domain="libcas.jnu.edu.cn", path='/cas')
	response_login = requests.post(url_lib, headers=headers, data=data_lib, cookies=cookie_lib)
	tree = etree.HTML(response_login.content)
	msg = tree.xpath("//div[@id='ltlMessage']/span[@id='msg']/text()")
	if msg != []:
		if msg[0] == u'账号或密码错误':
			return {'status': 102}
		elif msg[0] == u'验证码错误':
			return {'status': 101}
		else:
			return {'status': 103}
	sessionid_lib = response_login.history[-1].request._cookies["JSESSIONID"] # TODO: test needed
	sessionid_space = session_data['sessionid_space']
	user = User(id=session_data['id'], password_lib=session_data['passwd_lib'], password_space=session_data['passwd_space'],
	            sessionid_lib=sessionid_lib, sessionid_space=sessionid_space)
	user.save()
	return {'status': 0}
	# else: # space_login not in request, just update sessionid_lib
	# 	user = User.objects.get(id=session_data[0])
	# 	user.sessionid_lib = sessionid_lib
	# 	user.save()
	# 	return 0
def get_single_page(tree):
	result_dict = {}
	root_path = "//table[@class='table table-bordered table-hover table-striped iron-table']"

	for room_index in range(1,11):
		# TODO: overflow exception handle
		current_list = []
		current_room = tree.xpath(root_path + "/tbody/tr[$room]/td[@class='name']/center/text()", room=room_index)
		if current_room == []:
			break
		for hour_index in range(2,17):
			result = tree.xpath(root_path + "/tbody/tr[$room]/td[$hour]//div/@class", room=room_index, hour=hour_index)
			if result != []:
				if result[0] == 'allowreserve':
					current_list.append(1)
				else:
					current_list.append(0)
			else:
				current_list.append(0)
		result_dict[current_room[0][-3:]] = current_list # remove u‘研修室’'
	return result_dict
	# XXX: using bit may be faster than list


def get_room_table(date):
	url = "https://libsouthic.jnu.edu.cn"
	main_url = "https://libsouthic.jnu.edu.cn/ic?id=4"
	date_url = "https://libsouthic.jnu.edu.cn/ic/index.curdateindex/%s?id=4" # %s is a seq number string from HTML
	page_url = "https://libsouthic.jnu.edu.cn/ic/index.grid.pager/%d/%s?id=4" # %s are page index and seq number
	# the page seq num is from <div> @id
	xhr_headers = {
		'Origin': "https://libsouthic.jnu.edu.cn",
		'X-Requested-With': "XMLHttpRequest",
		'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
		'Content-type': "application/x-www-form-urlencoded",
		'Referer': "https://libsouthic.jnu.edu.cn/ic?id=4",
	}
	# get date_href
	request = urllib2.Request(url=main_url, headers=xhr_headers)
	html = urllib2.urlopen(request).read()
	html = html.decode('utf8')
	main_tree = etree.HTML(html)
	date_href = main_tree.xpath("//div[@id='actionzone']/table/tr/td[$date]/div/a/@href", date=date+2)[0]
	print date_href

	# get page_href list
	response = requests.post(url + date_href, data='t%3Azoneid=detailzone', headers=xhr_headers)
	html = json.loads(response.content)['content']
	date_tree = etree.HTML(html)
	page_href = date_tree.xpath('//table/parent::div/parent::div/@id')[0]
	pages = [url + date_href]
	page_index = 0
	while True:
		page_index = page_index + 1
		page_id = date_tree.xpath("//div[@class='t-data-grid-pager']/a[$i]/@id", i=page_index)
		if page_id == []:
			break
		pages.append(page_url % (page_index+1, page_href))
	# get cookie for every page and refresh date_url
	result_dict = dict()
	for page in pages:
		response = requests.post(page, headers= xhr_headers)
		jsessionid = None
		for k, v in response.cookies.items():
			if k == 'JSESSIONID':
				jsessionid = v
		cookie_jar = RequestsCookieJar()
		cookie_jar.set("JSESSIONID", jsessionid, domain="libsouthic.jnu.edu.cn")
		response = requests.post(url + date_href, data='t%3Azoneid=detailzone', headers=xhr_headers, cookies=cookie_jar)
		html = json.loads(response.content)['content']
		result_dict.update(get_single_page(etree.HTML(html)))
	return result_dict
	

def room_booking(date, room, start, end, jsessionid):
	hidden_base = [60, 66, 95, 108, 135]
	layer_room_num = int(room[-2:])
	if 205 >= int(room) >= 202:
		hidden = hidden_base[0] + layer_room_num
	elif 227 >= int(room) >= 216:
		hidden = hidden_base[1] + layer_room_num
	elif 313 >= int(room) >= 301:
		hidden = hidden_base[2] + layer_room_num
	elif 327 >= int(room) >= 316:
		hidden = hidden_base[3] + layer_room_num
	elif 427 >= int(room) >= 401:
		hidden = hidden_base[4] + layer_room_num
	else:
		print 'Wrong room number'
		return
	# TODO: limit date scope
	abs_date = (datetime.datetime.now() + datetime.timedelta(days=date)).strftime('%Y-%m-%d ')
	startdate = abs_date + str(start) +':00:00'
	enddate = abs_date + str(end) + ':00:00'

	url_booking = "https://libsouthic.jnu.edu.cn/user/reserve.reserveform"
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
		"Content-Type": "application/x-www-form-urlencoded",
		'X-Requested-With': "XMLHttpRequest",
	}
	data_booking = {
		"t:formdata": "qT85M15q6UFbt7NvA22jo+rLrFU=:H4sIAAAAAAAAAJVSsU7DMBC9RlCKulFagVgYypoy0AUWKiQEUoUQEQsLcuIjNUrsYDttWZiQ+AYWvgAxgcTegY1/4ANYGJgYcBqoWkIrdbF953fvPd/5/h1mO2UoxQpl7QjN2sbNFqMUuZKwLaRvk4h4LbQ1iVBpeVm3PSExYK7Zw0hw5FrZe/2K6qEUHirlxG7IlGKCn9yslrorz3kLck0oeoJrKYIDEqKGheY5aZNaQLhfc7Rk3N/qRhryqXhnCSojnvyYSMpNpbFVn2jLJQrthmuSxNO7DANadVDH0dpxr/hWfvnKeLmAK8gl2vMDkYnyjWnlM23pPdCNs8+7VwugG2W0lCZSU6JRJc5mjK9BZjw2gRY6FVgcuUZOh4nmfuJxuJTk73eQSJTgvxz5NByD+p9BJS/X03yofq90tnO3zsfy0+P1jgVWEwpewAx6n/YnaIaKAYYmMTLUQip+uj50/AbYYqzf9gIAAA==",
		"t:submit": "[\"submit_0\",\"submit_0\"]",
		"hidden": hidden,
		"startdate": startdate,
		"enddate": enddate,
		"reason": "",
		"t:zoneid": "reserveformzone"
	}
	cookie_jar = RequestsCookieJar()
	cookie_jar.set("JSESSIONID", jsessionid, domain="libsouthic.jnu.edu.cn")

	response_booking = requests.post(url_booking, data=data_booking, headers=headers, cookies=cookie_jar)
	if response_booking.status_code == 200:
		data = None
		try:
			data = json.loads(response_booking.content)
		except ValueError:
			return {'status': 2}     # not login
		if u'redirectURL' in data:
			return {'status': 0}     # success
		else:
			return {'status': 1}     # time conflict or others
	else:
		return {'status': -1}        # bad connection


def search_info(href):
	url_site = "https://opac.jnu.edu.cn/opac/book/" + href
	url_info = "https://opac.jnu.edu.cn/opac/book/getHoldingsInformation/"
	url_loc = "https://ifg.zhaobenshu.com/Find/find_ifc_GetSiteColl1.aspx?a=jnu&b=&c=%s&d=&x=josnp1365255842541256&y=1&z=YJmkd3Ngdy1557059656"

	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
	}

	try:
		response = requests.get(url_site, headers=headers)
		html = response.content
	except (HTTPError, URLError):
		print "Couldn't connect to opac.jnu.edu.cn."
		return
	print 'Connection Established \n *****'
	# html = html.decode('utf8')
	tree = etree.HTML(html)
	book_id = tree.xpath("//input[@id='bookId']/@value")[0]
	isbn = None
	summary = None
	for i in range(1,8):
		try:
			root_path = "//*[@id='detailsTable']/tr[%d]" % i
			if tree.xpath(root_path + "/th/text()") != [] and tree.xpath(root_path + "/th/text()")[0] == u'ISBN/价格：' :
				isbn = tree.xpath(root_path + "/td/text()")
				if len(isbn) != []:
					isbn = isbn[-1].split(':')[0]
			# if tree.xpath(root_path + "/th/text()") != [] and tree.xpath(root_path + "/th/text()")[0] == u'内容简介:':
			# 	summary = tree.xpath(root_path + "/td/text()")[0]
			# 	if tree.xpath(root_path + "/td/a") != []:
			# 		summary += '...'
		except IndexError:
			continue
	try:
		response_detail = requests.get(url_info + book_id, headers=headers)
	except (HTTPError, URLError):
		print "Couldn't connect to opac.jnu.edu.cn."
		return
	details = json.loads(response_detail.content)
	loc_str = ""
	result_status = []
	for detail in details:
		loc_str += '[#]' + detail[u'部门名称'] + '[*]' + detail[u'索书号'] + '[#]'
		result_status.append(detail["bookstatus"])
	response_loc = requests.get(url_loc % quote(loc_str.encode('utf8')), headers=headers)
	locations = json.loads(response_loc.content[response_loc.content.find('(') + 1: -2])
	result_loc = []
	if locations["error"] == "0":
		i = 0
		for loc in locations["find_ifc_GetSiteColl1_list1"]:
			result_loc.append({"location": loc["Sublib"] + loc["Room"] + loc["Site"], "status": result_status[i]})
			i += 1
	else:
		for detail in details:
			result_loc.append({"location": detail[u'部门名称'], "status": detail["bookstatus"]})
	result = dict()
	result['pic'] = "https://opac.jnu.edu.cn/opac/book/getImgByteById?bookId=%s&isbn=%s" % (book_id, isbn)
	# result['summary'] = summary
	# TODO: finish summary crawler
	result['libinfo'] = result_loc

	return result

def book_renew(sessionid_lib, book_id):
	success = '{"errorMessage":"续借成功","successed":true}'
	renewurl = "http://opac.jnu.edu.cn/opac/mylibrary/renewBook"
	reheaders = {
		"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
		"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
	}
	redata = {
		"barCode": book_id
	}
	jar = requests.cookies.RequestsCookieJar()
	jar.set('JSESSIONID', sessionid_lib, domain="opac.jnu.edu.cn", path='/')
	rsp = requests.post(renewurl, headers=reheaders, data=redata, cookies=jar)
	if rsp.status_code != 200:
		return {'status': -1} # bad connection
	rsp = rsp.content.decode()
	if '读者登录' in rsp: # XXX: use xpath
		return  {'status': 1} # not login
	if rsp == success:
		return {'status': 0} # success
	else:
		return {'status': 2} #can't renew again

	# 0 -> ok 1 -> not login 2 -> can't renew again -1 -> bad connection

def book_renew_search(sessionid_lib):
	'''
	:param sessionid_lib:
	:return: 书名和条形码及时间组成的data
	'''
	baseurl = "http://opac.jnu.edu.cn/opac/mylibrary/borrowBooks"
	baseheaders = {
		"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
		"Connection": "keep-alive"
	}
	jar = requests.cookies.RequestsCookieJar()
	jar.set('JSESSIONID', sessionid_lib, domain="opac.jnu.edu.cn", path='/')
	rsp = requests.get(baseurl, headers=baseheaders,cookies = jar)
	if rsp.status_code != 200:
		return {"status": -1}
	rsp = rsp.content.decode()
	if '读者登录' in rsp: # XXX: use xpath
		return {"status": 1}
	html = etree.HTML(rsp)
	html_data = html.xpath('//tr')

	result = []
	for i in range(1, len(html_data)):
		book_name = html_data[i].xpath('//td[2]/a/text()')[0]
		book_id = html_data[i].xpath('//td[3]/text()')[0]
		book_expire_time = html_data[i].xpath('//td[4]/text()')[0]
		book_renew_times = html_data[i].xpath('//td[6]/text()')[0]
		data = dict()
		data["book_name"] = book_name
		data["book_id"] = book_id
		data["book_expire_time"] = book_expire_time
		data["book_renew_times"] = book_renew_times
		result.append(data)
	return {'status': 0, 'table': result}
		
