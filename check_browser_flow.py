# -*- coding: utf-8 -*-
import http.cookiejar, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://127.0.0.1:5000'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def request(path, jar, data=None):
    opener = urllib.request.build_opener(NoRedirect, urllib.request.HTTPCookieProcessor(jar))
    if data is None:
        req = urllib.request.Request(BASE + path)
    else:
        req = urllib.request.Request(BASE + path, data=urllib.parse.urlencode(data).encode())
    try:
        r = opener.open(req)
        return r.getcode(), r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

jar = http.cookiejar.CookieJar()
_, body = request('/login', jar)
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
code, _ = request('/login', jar, {'csrf_token': m.group(1), 'email': 'a@xyz.com', 'password': '123456'})
print('login:', code)

code, body = request('/manage/events/new', jar)
print('GET /manage/events/new:', code, '| có form:', 'id="eventForm"' in body, '| có hidden csrf:', 'name="csrf_token"' in body)
m2 = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
token = m2.group(1) if m2 else '(KHÔNG CÓ)'
print('token từ form:', token[:20] + '...' if len(token) > 20 else token)

now = datetime.now()
bad = {
    'csrf_token': token,
    'name': '',
    'description': 'test',
    'location': 'test',
    'start_time': (now + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M'),
    'end_time': (now + timedelta(days=14, hours=3)).strftime('%Y-%m-%dT%H:%M'),
    'registration_deadline': (now + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
    'max_attendees': '10',
    'target_audience': 'Toàn công ty',
}
code, body = request('/manage/events/new', jar, bad)
print('POST thiếu tên:', code, '| có "Vui lòng nhập tên sự kiện":', 'Vui lòng nhập tên sự kiện' in body, '| có is-invalid:', 'is-invalid' in body)

good = dict(bad); good['name'] = 'Kiểm tra trình duyệt ' + now.strftime('%H%M%S')
code, _ = request('/manage/events/new', jar, good)
print('POST hợp lệ:', code, '(302 = thành công)')

code, body = request('/manage/events', jar)
print('GET /manage/events sau tạo:', code, '| có flash thành công:', 'Tạo sự kiện thành công' in body, '| có sự kiện mới:', 'Kiểm tra trình duyệt' in body)
