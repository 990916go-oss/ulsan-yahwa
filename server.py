#!/usr/bin/env python3
"""Ulsan Yahwa demo server; stdlib only, SQLite persistence."""
import os,json,sqlite3,secrets,hashlib,hmac,time,re,threading,mimetypes
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from http.cookies import SimpleCookie
ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('YAHWA_DB_PATH',str(ROOT/'yahwa.sqlite3')))
PASSWORD=os.environ.get('YAHWA_ADMIN_PASSWORD','')
if len(PASSWORD)<12: raise SystemExit('Set YAHWA_ADMIN_PASSWORD to at least 12 characters before starting.')
PORT=int(os.environ.get('PORT','8000'))
NAMES=['이비자','퍼스트','크크','구구단','디올','유앤미','강남스타일','유빠','무희','6F 육층','미술관','컴퍼니','우성','부성','달동 시그니처','무거 라운지','울산 오션','울산 러시아','울산 태국','울산 다국적','자전거','봉자','일반 노래방']
lock=threading.Lock(); sessions={}
def connect():
 c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;return c
def setup():
 with connect() as c:
  c.execute('CREATE TABLE IF NOT EXISTS venues(id INTEGER PRIMARY KEY,name TEXT NOT NULL,people INTEGER,reservations INTEGER,price INTEGER,tc INTEGER,hours TEXT,parking TEXT,updated TEXT)')
  c.execute('CREATE TABLE IF NOT EXISTS notices(id INTEGER PRIMARY KEY AUTOINCREMENT,body TEXT NOT NULL,created INTEGER NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY AUTOINCREMENT,venue INTEGER NOT NULL,rating INTEGER NOT NULL,nick TEXT NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,created INTEGER NOT NULL,status TEXT NOT NULL DEFAULT "pending")')
  c.execute('CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,detail TEXT NOT NULL,created INTEGER NOT NULL)')
  for i,name in enumerate(NAMES,1): c.execute('INSERT OR IGNORE INTO venues(id,name,price,tc,hours) VALUES(?,?,?,?,?)',(i,name,170000 if i==1 else None,110000 if i==1 else None,'24시간 (운영자 제공 정보)' if i==1 else '확인 필요'))
DB.parent.mkdir(parents=True,exist_ok=True)
setup()
class Handler(BaseHTTPRequestHandler):
 def send(self,status,data,cookie=None):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(raw)))
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers();self.wfile.write(raw)
 def body(self):
  n=int(self.headers.get('Content-Length','0'));return json.loads(self.rfile.read(n)) if 0<n<=20000 else {}
 def sid(self):
  try:c=SimpleCookie();c.load(self.headers.get('Cookie',''));return c['yahwa_sid'].value
  except:return ''
 def auth(self):
  sid=self.sid()
  with lock:
   for k,v in list(sessions.items()):
    if v['expiry']<time.time():sessions.pop(k,None)
   return sessions.get(sid)
 def guard(self):
  sess=self.auth()
  if not sess:self.send(401,{'error':'관리자 로그인이 필요합니다'});return False
  if self.headers.get('X-CSRF-Token')!=sess['csrf']:self.send(403,{'error':'보안 토큰 오류'});return False
  return True
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/robots.txt':
   base=os.environ.get('SITE_URL','').rstrip('/')
   content=('User-agent: *\nAllow: /\nDisallow: /admin.html\nDisallow: /api/\n'+('Sitemap: '+base+'/sitemap.xml\n' if base else '')).encode()
   self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content);return
  if path=='/sitemap.xml':
   from xml.sax.saxutils import escape
   base=os.environ.get('SITE_URL','').rstrip('/')
   if not base:self.send_error(503,'SITE_URL is not configured');return
   content=('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+escape(base)+'/</loc></url></urlset>').encode()
   self.send_response(200);self.send_header('Content-Type','application/xml; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content);return
  if path=='/api/public':
   with connect() as c:
    self.send(200,{'venues':[dict(x) for x in c.execute('SELECT * FROM venues ORDER BY id')],'notices':[dict(x) for x in c.execute('SELECT * FROM notices ORDER BY id DESC LIMIT 20')],'reviews':[dict(x) for x in c.execute("SELECT id,venue,rating,nick,title,body,created FROM reviews WHERE status='approved' ORDER BY id DESC LIMIT 200")]});return
  if path=='/api/me':
   a=self.auth();self.send(200,{'authenticated':bool(a),'csrf':a['csrf'] if a else None});return
  if path=='/api/admin':
   if not self.auth():self.send(401,{'error':'로그인 필요'});return
   with connect() as c:self.send(200,{'venues':[dict(x) for x in c.execute('SELECT * FROM venues')],'notices':[dict(x) for x in c.execute('SELECT * FROM notices ORDER BY id DESC')],'reviews':[dict(x) for x in c.execute('SELECT * FROM reviews ORDER BY id DESC LIMIT 500')],'audit':[dict(x) for x in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 50')]});return
  if path=='/':path='/index.html'
  if path not in ('/index.html','/admin.html') and not path.startswith('/assets/'):self.send_error(404);return
  f=(ROOT/path.lstrip('/')).resolve()
  if not f.is_relative_to(ROOT) or not f.is_file():self.send_error(404);return
  raw=f.read_bytes()
  if path=='/index.html':raw=raw.replace(b'__SITE_URL__',os.environ.get('SITE_URL','').rstrip('/').encode())
  self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(f.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(raw)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  path=urlparse(self.path).path
  try:d=self.body()
  except:self.send(400,{'error':'JSON 형식 오류'});return
  if path=='/api/login':
   if not hmac.compare_digest(str(d.get('password','')),PASSWORD):time.sleep(.3);self.send(401,{'error':'비밀번호가 틀렸습니다'});return
   sid=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
   with lock:sessions[sid]={'csrf':csrf,'expiry':time.time()+8*3600}
   self.send(200,{'ok':True,'csrf':csrf},'yahwa_sid='+sid+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+('; Secure' if os.environ.get('YAHWA_HTTPS')=='1' else ''));return
  if path=='/api/review':
   try:
    v=int(d.get('venue'));rating=int(d.get('rating'));nick=str(d.get('nick','')).strip();title=str(d.get('title','')).strip();body=str(d.get('body','')).strip()
    if not(1<=v<=23 and 1<=rating<=5 and 2<=len(nick)<=30 and 3<=len(title)<=100 and 10<=len(body)<=1500):raise ValueError()
   except:self.send(400,{'error':'후기 입력값을 확인하세요'});return
   with connect() as c:c.execute('INSERT INTO reviews(venue,rating,nick,title,body,created) VALUES(?,?,?,?,?,?)',(v,rating,nick,title,body,int(time.time()*1000)))
   self.send(201,{'ok':True,'message':'관리자 승인 후 공개됩니다'});return
  if not self.guard():return
  if path=='/api/logout':
   with lock:sessions.pop(self.sid(),None)
   self.send(200,{'ok':True},'yahwa_sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0');return
  with connect() as c:
   if path=='/api/venue':
    try:
     vid=int(d.get('id'))
     if vid not in range(1,24):raise ValueError()
     vals=[]
     for key in ('people','reservations','price','tc'):
      value=d.get(key);value=None if value in ('',None) else int(value)
      if value is not None and not(0<=value<=100000000):raise ValueError()
      vals.append(value)
     hours=str(d.get('hours',''))[:100];parking=str(d.get('parking',''))[:100]
    except:self.send(400,{'error':'입력값 오류'});return
    c.execute('UPDATE venues SET people=?,reservations=?,price=?,tc=?,hours=?,parking=?,updated=? WHERE id=?',(*vals,hours,parking,time.strftime('%Y-%m-%d %H:%M'),vid))
    c.execute('INSERT INTO audit(action,detail,created) VALUES(?,?,?)',('venue',str(vid),int(time.time())))
   elif path=='/api/notice':
    body=str(d.get('body','')).strip()
    if not 1<=len(body)<=500:self.send(400,{'error':'공지 내용 1~500자'});return
    c.execute('INSERT INTO notices(body,created) VALUES(?,?)',(body,int(time.time())))
   elif path=='/api/notice/delete':
    c.execute('DELETE FROM notices WHERE id=?',(int(d.get('id',0)),))
   elif path=='/api/review/status':
    status=d.get('status')
    if status not in ('approved','rejected','pending'):self.send(400,{'error':'상태 오류'});return
    c.execute('UPDATE reviews SET status=? WHERE id=?',(status,int(d.get('id',0))))
   else:self.send(404,{'error':'경로 없음'});return
  self.send(200,{'ok':True})
if __name__=='__main__':
 print(f'Open http://localhost:{PORT}/admin.html (admin) and http://localhost:{PORT}/ (public)')
 ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
