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

def get_csrf(path, jar):
    _, body = request(path, jar)
    m = re.search(r'name="csrf-token" content="([^"]+)"', body) or re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
    return m.group(1) if m else '', body

jar = http.cookiejar.CookieJar()
_, body = request('/login', jar)
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
request('/login', jar, {'csrf_token': m.group(1), 'email': 'a@xyz.com', 'password': '123456'})

def errors_in(body):
    msgs = re.findall(r'invalid-feedback[^>]*>\s*([^<]+)', body)
    return [x.strip() for x in msgs if x.strip()]

now = datetime.now()
def fmt(t): return t.strftime('%Y-%m-%dT%H:%M')

def try_case(label, deadline, start, end, expect_ok):
    token, _ = get_csrf('/manage/events/new', jar)
    fields = {
        'csrf_token': token, 'name': 'Test ma trận ' + label.replace(' ', '-'),
        'description': 'test', 'location': 'test',
        'start_time': fmt(start), 'end_time': fmt(end),
        'registration_deadline': fmt(deadline),
        'max_attendees': '10', 'target_audience': 'Toàn công ty',
    }
    code, body = request('/manage/events/new', jar, fields)
    errs = errors_in(body)
    status = 'OK(302)' if code == 302 else ('LỖI: ' + ' | '.join(errs) if errs else 'LỖI không rõ, code=' + str(code))
    mark = 'PASS-KỲ-VỌNG' if (code == 302) == expect_ok else '!!! KHÁC KỲ VỌNG'
    print(label + ': ' + status + '  [' + mark + ']')

print('now =', now.strftime('%d/%m/%Y %H:%M:%S'))
print()
try_case('A deadline=now+2h < start', now + timedelta(hours=2), now + timedelta(days=3), now + timedelta(days=3, hours=2), True)
try_case('B deadline=now+3d+1h > start', now + timedelta(days=3, hours=1), now + timedelta(days=3), now + timedelta(days=3, hours=2), False)
try_case('C deadline có giây (:00)', now + timedelta(hours=2), now + timedelta(days=3), now + timedelta(days=3, hours=2), None)
try_case('D deadline=now+5phút (sát hiện tại)', now + timedelta(minutes=5), now + timedelta(days=3), now + timedelta(days=3, hours=2), True)
try_case('E end < start', now + timedelta(hours=2), now + timedelta(days=3), now + timedelta(hours=30), False)

# Case C thực tế: gửi chuỗi có giây
token, _ = get_csrf('/manage/events/new', jar)
fields = {
    'csrf_token': token, 'name': 'Test giay',
    'description': 'test', 'location': 'test',
    'start_time': (now + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
    'end_time': (now + timedelta(days=3, hours=2)).strftime('%Y-%m-%dT%H:%M'),
    'registration_deadline': (now + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S'),
    'max_attendees': '10', 'target_audience': 'Toàn công ty',
}
code, body = request('/manage/events/new', jar, fields)
print('C-thật (chuỗi có giây): code=' + str(code) + ' | lỗi: ' + ' | '.join(errors_in(body)))
