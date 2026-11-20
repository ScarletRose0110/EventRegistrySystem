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
        return r.getcode(), r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

def login(jar, email, password):
    _, body = request('/login', jar)
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', body)
    token = m.group(1) if m else ''
    return request('/login', jar, {'csrf_token': token, 'email': email, 'password': password})

results = []
def check(name, ok, detail=''):
    results.append(ok)
    print(('PASS' if ok else 'FAIL') + ' | ' + name + (' | ' + detail if detail else ''))

jar = http.cookiejar.CookieJar()
login(jar, 'a@xyz.com', '123456')

code, body = request('/events', jar)
check('/events → 200', code == 200, 'code=' + str(code))
check('Danh sách có card-event (adaptive card)', 'card-event' in body)
check('Danh sách có status-badge (huy hiệu trạng thái)', 'status-badge' in body)
check('Danh sách có event-meta (icon meta)', 'event-meta' in body)
check('Không còn lỗi undefined', 'UndefinedError' not in body and 'status_key' not in body)

code, body = request('/events/1', jar)
check('/events/1 chi tiết → 200', code == 200, 'code=' + str(code))
check('Chi tiết có detail-card + meta-block', 'detail-card' in body and 'meta-block' in body)
check('Chi tiết hiển thị huy hiệu trạng thái', 'status-badge' in body)

jar2 = http.cookiejar.CookieJar()
login(jar2, 'b@xyz.com', '123456')
code, body = request('/manage/events', jar2)
check('b vào /manage/events → 403', code == 403)
check('Trang 403 có error-card mới', 'error-card' in body)

jar3 = http.cookiejar.CookieJar()
code, body = request('/events/999999', jar3)
check('Không tồn tại → 302', code == 302)

failed = len(results) - sum(results)
print('TỔNG: ' + str(sum(results)) + ' PASS / ' + str(failed) + ' FAIL')
sys.exit(1 if failed else 0)
