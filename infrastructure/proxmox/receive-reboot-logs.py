import http.server,pathlib,datetime,os,threading,uuid,argparse,shlex
parser=argparse.ArgumentParser(description='Temporary source-restricted LAN diagnostic receiver')
parser.add_argument('--bind',required=True)
parser.add_argument('--port',type=int,default=18831)
parser.add_argument('--allow-ip',action='append',required=True)
parser.add_argument('--output-dir',type=pathlib.Path,required=True)
parser.add_argument('--collector',type=pathlib.Path,required=True)
parser.add_argument('--lifetime',type=int,default=1800)
args=parser.parse_args()
BASE=args.output_dir
BASE.mkdir(parents=True,exist_ok=True,mode=0o700)
os.chmod(BASE,0o700)
ALLOWED=set(args.allow_ip)
class Handler(http.server.BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def reply(self,status,data):
  self.send_response(status);self.send_header('Content-Length',str(len(data)));self.send_header('Connection','close');self.end_headers();self.wfile.write(data);self.close_connection=True
 def do_GET(self):
  if self.client_address[0] not in ALLOWED or self.path!='/collect.sh':return self.reply(403,b'Denied\n')
  body=("export PX30_UPLOAD_URL="+shlex.quote(f"http://{args.bind}:{args.port}/capture")+"\n").encode()+args.collector.read_bytes();self.reply(200,body)
 def do_PUT(self):
  if self.client_address[0] not in ALLOWED or self.path!='/capture':return self.reply(403,b'Denied\n')
  name='px30-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
  suffix={"application/gzip":".tar.gz","application/zstd":".tar.zst"}.get(self.headers.get('Content-Type'),".log")
  path=BASE/(name+'.partial'+suffix);self.connection.settimeout(20);total=0
  try:
   with path.open('xb') as f:
    os.chmod(path,0o600)
    if self.headers.get('Transfer-Encoding','').lower()=='chunked':
     while True:
      line=self.rfile.readline(128)
      if not line:raise EOFError('connection ended between chunks')
      size=int(line.strip().split(b';',1)[0],16)
      if size==0:break
      if total+size>2*1024**3:raise ValueError('2 GiB capture limit')
      remaining=size
      while remaining:
       data=self.rfile.read(min(remaining,65536))
       if not data:raise EOFError('connection ended within chunk')
       f.write(data);f.flush();total+=len(data);remaining-=len(data)
      if self.rfile.read(2)!=b'\r\n':raise ValueError('invalid chunk terminator')
    else:
     remaining=int(self.headers.get('Content-Length','0'))
     if remaining<0 or remaining>2*1024**3:raise ValueError('invalid capture length')
     while remaining:
      data=self.rfile.read(min(remaining,65536))
      if not data:raise EOFError('connection ended')
      f.write(data);f.flush();total+=len(data);remaining-=len(data)
   path=path.rename(BASE/(name+suffix));print('Received',path.name,total,'bytes',flush=True)
   self.reply(201,('Saved on dev: '+str(path)+'\n').encode())
  except (OSError,ValueError,EOFError) as e:
   print('Partial preserved',path.name,total,type(e).__name__,flush=True)
   try:self.reply(400,b'Connection interrupted; received data preserved on dev\n')
   except OSError:pass
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer((args.bind,args.port),Handler)
threading.Timer(args.lifetime,server.shutdown).start()
print('LAN-only diagnostic receiver ready; expires after 30 minutes',flush=True)
server.serve_forever();server.server_close()
