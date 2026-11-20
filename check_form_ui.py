# -*- coding: utf-8 -*-
import http.cookiejar, re, sys, urllib.error, urllib.parse, urllib.request
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
        return r.getcode(), dict(r.headers), r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode('utf-8')

jar = http.cookiejar.CookieJar()
_, _, body = request('/login', jar)
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
request('/login', jar, {'csrf_token': m.group(1), 'email': 'a@xyz.com', 'password': '123456'})
code, headers, body = request('/manage/events/new', jar)
print('form mới: code=' + str(code))
print('  Cache-Control:', headers.get('Cache-Control', '(không có)'))
print('  có formAlert:', 'formAlert' in body)
print('  có is-invalid JS:', 'classList.add' in body)
print('  KHÔNG còn alert():', 'alert(' not in body)
