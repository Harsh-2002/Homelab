const crypto = require('node:crypto');
const path = require('node:path');
const {kv} = require('orva');
const {S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand} = require('@aws-sdk/client-s3');
const MAX_BYTES = 4 * 1024 * 1024;
const MAX_EXPIRY = 7 * 86400;
const ALLOWED = new Set(['image/jpeg','image/png','image/webp','image/gif','image/avif','image/bmp','image/tiff','image/heic','image/heif','image/svg+xml','application/pdf','text/plain','text/markdown','text/csv','application/json','application/xml','text/xml','application/rtf','application/msword','application/vnd.ms-excel','application/vnd.ms-powerpoint','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.oasis.opendocument.text','application/vnd.oasis.opendocument.spreadsheet','application/vnd.oasis.opendocument.presentation']);
function response(statusCode,body,type='application/json; charset=utf-8'){
 return {statusCode,headers:{'Content-Type':type,'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff'},body};
}
function storage(){
 if(!process.env.S3_ACCESS_KEY||!process.env.S3_SECRET_KEY||!process.env.S3_BUCKET||!process.env.S3_ENDPOINT)throw new Error('Storage configuration missing');
 const client=new S3Client({endpoint:process.env.S3_ENDPOINT,region:process.env.S3_REGION||'us-east-1',forcePathStyle:true,credentials:{accessKeyId:process.env.S3_ACCESS_KEY,secretAccessKey:process.env.S3_SECRET_KEY},requestChecksumCalculation:'WHEN_REQUIRED',responseChecksumValidation:'WHEN_REQUIRED',maxAttempts:2});
 return {client,Bucket:process.env.S3_BUCKET};
}
async function send(s,command){return s.client.send(command,{abortSignal:AbortSignal.timeout(18000)});}
async function download(token){
 if(!/^[A-Za-z0-9_-]{22}$/.test(token))return response(404,{error:'Share not found.'});
 try{
  const state=await kv.get('share:'+token,null);
  if(!state)return response(404,{error:'Share not found or expired.'});
  if(state.expiresAt<=Date.now())return response(410,{error:'This share has expired.'});
  if(!/^quick-share\/[a-f0-9]{48}(\.[a-z0-9]{1,10})?$/.test(state.key))return response(404,{error:'Share not found.'});
  const s=storage();
  const object=await send(s,new GetObjectCommand({Bucket:s.Bucket,Key:state.key}));
  const type=state.type||'application/octet-stream';
  const disposition=type.startsWith('image/')&&type!=='image/svg+xml'?'inline':'attachment';
  const safeName=encodeURIComponent(state.name||'download').replace(/['()*]/g,c=>'%'+c.charCodeAt(0).toString(16).toUpperCase());
  return (async function*(){
   yield {statusCode:200,headers:{'Content-Type':type,'Content-Disposition':disposition+"; filename*=UTF-8''"+safeName,'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff'},body:''};
   try{for await(const chunk of object.Body)yield chunk;}
   finally{object.Body.destroy?.();}
  })();
 }catch(e){
  console.error('share read failed',e.name,e.$metadata?.httpStatusCode);
  if(e.name==='NoSuchKey'||e.$metadata?.httpStatusCode===404)return response(404,{error:'Share not found.'});
  return response(502,{error:'File is temporarily unavailable. Try again.'});
 }
}
async function cleanup(s){
 let cursor='',deleted=0,failed=0,examined=0;
 do{
  const page=await kv.list({prefix:'share:',limit:100,cursor});
  for(const entry of page.keys){
   const state=entry.value;
   examined++;
   if(!state||state.expiresAt>Date.now())continue;
   if(!/^quick-share\/[a-f0-9]{48}(\.[a-z0-9]{1,10})?$/.test(state.key)){failed++;continue;}
   try{
    await send(s,new DeleteObjectCommand({Bucket:s.Bucket,Key:state.key}));
    await kv.delete(entry.key);deleted++;
   }catch(e){failed++;console.error('cleanup failed',e.name,e.$metadata?.httpStatusCode);}
  }
  cursor=page.nextCursor;
 }while(cursor&&examined<1000);
 return {deleted,failed};
}

const HTML = "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\"><title>Quick Share</title><style>:root{color-scheme:light dark;--bg:#f7f7f5;--card:#fff;--text:#171717;--muted:#777;--line:#d8d8d3;--soft:#f0f0ed}@media(prefers-color-scheme:dark){:root{--bg:#111;--card:#171717;--text:#f3f3f1;--muted:#92928d;--line:#343430;--soft:#222220}}*{box-sizing:border-box}html,body{margin:0;min-height:100%;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif;background:var(--bg);color:var(--text)}body{min-height:100vh;display:grid;place-items:center;padding:18px}main{width:min(100%,440px)}.drop{min-height:205px;background:var(--card);border:1.5px dashed var(--line);border-radius:18px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:28px;cursor:pointer;transition:.15s ease}.drop:hover,.drop.drag{border-color:var(--text);transform:translateY(-1px)}.icon{width:42px;height:42px;border-radius:12px;background:var(--soft);display:grid;place-items:center;font-size:22px;margin-bottom:16px}.title{font-size:15px;font-weight:650}.sub{font-size:13px;color:var(--muted);margin-top:7px}input[type=file]{display:none}.status{display:none;margin-top:12px;padding:14px;background:var(--card);border:1px solid var(--line);border-radius:14px}.name{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.detail{font-size:12px;color:var(--muted);margin-top:4px}.progress{height:3px;background:var(--soft);border-radius:999px;overflow:hidden;margin-top:12px}.bar{height:100%;width:100%;transform:scaleX(0);transform-origin:left;background:var(--text);transition:transform .12s ease}.result{display:none;gap:8px;margin-top:12px}.url{min-width:0;flex:1;border:1px solid var(--line);background:var(--card);color:var(--text);border-radius:12px;padding:12px 13px;font-size:13px;outline:none}button{border:0;border-radius:12px;padding:0 16px;background:var(--text);color:var(--bg);font-weight:650;cursor:pointer}.error{display:none;color:#d44;font-size:13px;text-align:center;margin-top:10px}@media(max-width:480px){.drop{min-height:190px}.result{flex-direction:column}.result button{height:44px}.url{width:100%}}.expiry{display:flex;align-items:center;justify-content:space-between;margin:18px 0;font-size:16px}.expiry select{font:inherit;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text)}:focus-visible{outline:2px solid var(--text);outline-offset:3px}.url{font-size:16px}input[type=file]{display:block;width:100%;margin-top:16px;font-size:14px}\nheader{margin-bottom:28px}h1{font-size:30px;line-height:1.1;letter-spacing:-.03em;font-weight:650;margin:0 0 10px}header p{font-size:16px;line-height:1.5;color:var(--muted);margin:0}\n:root{--muted:#62625d;--accent:#087f75}@media(prefers-color-scheme:dark){:root{--muted:#a5a59e;--accent:#75d7c9}}\nmain{width:min(100%,460px)}.drop{min-height:220px;border-radius:16px;transition:border-color .16s ease,background .16s ease}.drop:hover,.drop.drag{border-color:var(--accent);background:var(--soft);transform:none}.icon{background:none;color:var(--accent);width:44px;height:44px;margin-bottom:18px}.icon svg{width:32px;height:32px}.title{font-size:17px;line-height:1.5}.sub{font-size:14px;line-height:1.5}.expiry{margin:22px 0}.expiry select{min-height:44px;padding:8px 12px}.name{font-size:15px;line-height:1.5}.detail{font-size:14px;line-height:1.5}.status{border-radius:12px;padding:16px}.progress{margin-top:16px;height:4px}.bar{background:var(--accent)}.result{margin-top:16px}.result button{white-space:nowrap;min-height:44px}.result button:hover{opacity:.85}.url{min-height:44px;font-size:16px}.error{font-size:14px;line-height:1.6;text-align:left}.privacy{font-size:13px;line-height:1.6;color:var(--muted);margin:20px 0 0;max-width:46ch}::selection{background:var(--accent);color:var(--bg)}input,select{caret-color:var(--accent)}button:disabled{opacity:.55;cursor:wait}\n@media(prefers-reduced-motion:reduce){*{transition:none!important}}\n@media(max-width:480px){body{padding:24px}h1{font-size:28px}.drop{min-height:220px}}\n</style></head><body><main><header><h1>Quick Share</h1><p>One file. One temporary link.</p></header><label class=\"drop\" id=\"drop\" for=\"file\"><div class=\"icon\" aria-hidden=\"true\"><svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M12 16V3m-5 5 5-5 5 5M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4\"/></svg></div><div class=\"title\">Drop a file or choose one</div><div class=\"sub\">Images & documents · max 4 MiB</div><input id=\"file\" type=\"file\" accept=\"image/*,.pdf,.txt,.md,.csv,.json,.xml,.rtf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp\"></label><label class=\"expiry\" for=\"expiry\">Link expires after <select id=\"expiry\"><option value=\"3600\">1 hour</option><option value=\"21600\">6 hours</option><option value=\"86400\">1 day</option><option value=\"259200\">3 days</option><option value=\"604800\">7 days</option></select></label><section aria-live=\"polite\" class=\"status\" id=\"status\"><div class=\"name\" id=\"name\"></div><div class=\"detail\" id=\"detail\">Preparing…</div><div class=\"progress\"><div class=\"bar\" id=\"bar\"></div></div></section><div class=\"result\" id=\"result\"><input class=\"url\" id=\"url\" aria-label=\"Share link\" readonly><button id=\"copy\" type=\"button\">Copy link</button></div><div role=\"alert\" class=\"error\" id=\"error\"></div><p class=\"privacy\">Anyone with the link can access the file until it expires. Expired files are automatically deleted.</p></main><script>const MAX=4*1024*1024,$=id=>document.getElementById(id),input=$(\"file\"),drop=$(\"drop\"),statusEl=$(\"status\"),nameEl=$(\"name\"),detail=$(\"detail\"),bar=$(\"bar\"),result=$(\"result\"),urlEl=$(\"url\"),copy=$(\"copy\"),errorEl=$(\"error\");function human(n){return n<1024?n+\" B\":n<1048576?(n/1024).toFixed(1)+\" KB\":(n/1048576).toFixed(1)+\" MB\"}function fail(m){errorEl.textContent=m;errorEl.style.display=\"block\";detail.textContent=\"Upload failed\";bar.style.transform=\"scaleX(0)\"}function reset(){errorEl.style.display=\"none\";result.style.display=\"none\";bar.style.transform=\"scaleX(0)\";copy.textContent=\"Copy link\"}\nlet busy=false;\nasync function upload(file){\n if(busy)return;reset();if(!file)return;\n if(file.size<1)return fail(\"The file is empty.\");\n if(file.size>MAX)return fail(\"File must be 4 MiB or smaller.\");\n busy=true;input.disabled=true;$(\"expiry\").disabled=true;\n statusEl.style.display=\"block\";nameEl.textContent=file.name;\n try{\n  detail.textContent=human(file.size)+\" · preparing\";\n  const data=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(\",\")[1]);r.onerror=()=>reject(new Error(\"Could not read the file.\"));r.readAsDataURL(file)});\n  const b=await new Promise((resolve,reject)=>{\n   const x=new XMLHttpRequest();x.open(\"POST\",location.href,true);x.timeout=45000;x.setRequestHeader(\"Content-Type\",\"application/json\");\n   x.upload.onprogress=e=>{if(e.lengthComputable)bar.style.transform=\"scaleX(\"+(e.loaded/e.total*0.9)+\")\"};\n   x.onload=()=>{let b;try{b=JSON.parse(x.responseText)}catch{return reject(new Error(\"Server returned an invalid response.\"))}\n    if(x.status>=200&&x.status<300)resolve(b);else reject(new Error(b.error||(\"Request failed (\"+x.status+\"). Choose the file again to retry.\")))};\n   x.onerror=()=>reject(new Error(\"Network error. Choose the file again to retry.\"));\n   x.ontimeout=()=>reject(new Error(\"Upload timed out. Choose the file again to retry.\"));\n   detail.textContent=human(file.size)+\" · uploading\";\n   x.send(JSON.stringify({name:file.name,type:file.type,size:file.size,expiresIn:Number($(\"expiry\").value),data}));\n  });\n  bar.style.transform=\"scaleX(1)\";detail.textContent=\"Uploaded · expires \"+new Date(b.expiresAt).toLocaleString();\n  urlEl.value=b.url;result.style.display=\"flex\";\n }catch(e){fail(e.message||\"Upload failed. Choose the file again to retry.\")}\n finally{busy=false;input.disabled=false;$(\"expiry\").disabled=false;input.value=\"\"}\n}\ninput.addEventListener(\"change\",()=>upload(input.files[0]));[\"dragenter\",\"dragover\"].forEach(v=>drop.addEventListener(v,e=>{e.preventDefault();drop.classList.add(\"drag\")}));[\"dragleave\",\"drop\"].forEach(v=>drop.addEventListener(v,e=>{e.preventDefault();drop.classList.remove(\"drag\")}));drop.addEventListener(\"drop\",e=>upload(e.dataTransfer.files[0]));copy.addEventListener(\"click\",async()=>{try{await navigator.clipboard.writeText(urlEl.value);copy.textContent=\"Copied\";setTimeout(()=>copy.textContent=\"Copy link\",1200)}catch{urlEl.select();document.execCommand(\"copy\")}});</script></body></html>";

exports.handler=async(event)=>{
 const method=String(event.method||'GET').toUpperCase();
 const pathname=String(event.path||'/').split('?')[0];
 if(method==='GET'&&pathname.startsWith('/s/'))return download(pathname.slice(3));
 if(method==='GET')return response(200,HTML,'text/html; charset=utf-8');
 if(method!=='POST')return response(405,{error:'Method not allowed.'});
 let body;try{body=JSON.parse(event.body||'{}')}catch{return response(400,{error:'Invalid JSON.'})}
 if(!body||typeof body!=='object'||Array.isArray(body))return response(400,{error:'Invalid request.'});
 if(body.action==='cleanup'&&event.headers?.['x-orva-trigger']!=='cron')return response(403,{error:'Cleanup is scheduled only.'});
 let s;try{s=storage()}catch{return response(503,{error:'Storage is not configured.'})}
 try{
  if(body.action==='cleanup'){
   const result=await cleanup(s);
   return response(result.failed?503:200,result);
  }
  const {name,type,size,data}=body,expiresIn=body.expiresIn??3600;
  if(typeof name!=='string'||!name.trim()||name.length>255)return response(400,{error:'Invalid filename.'});
  if(!ALLOWED.has(type))return response(415,{error:'Unsupported file type.'});
  if(!Number.isInteger(size)||size<1||size>MAX_BYTES)return response(400,{error:'File must be 4 MiB or smaller.'});
  if(!Number.isInteger(expiresIn)||expiresIn<60||expiresIn>MAX_EXPIRY)return response(400,{error:'Expiry must be between 1 minute and 7 days.'});
  if(typeof data!=='string'||data.length!==4*Math.ceil(size/3)||!/^[A-Za-z0-9+/]*={0,2}$/.test(data))return response(400,{error:'Invalid file data.'});
  const bytes=Buffer.from(data,'base64');
  if(bytes.length!==size)return response(400,{error:'File size does not match.'});
  const id=crypto.randomBytes(16).toString('base64url'),objectId=crypto.randomBytes(24).toString('hex'),ext=path.extname(name).toLowerCase();
  const key='quick-share/'+objectId+(/^\.[a-z0-9]{1,10}$/.test(ext)?ext:'');
  const expiresAt=Date.now()+expiresIn*1000;
  await kv.put('share:'+id,{key,expiresAt,name,type},{ttlSeconds:0});
  await send(s,new PutObjectCommand({Bucket:s.Bucket,Key:key,Body:bytes,ContentType:type}));
  const url='https://orva.l3b.cc.cd/fn/01a110c1-cc79-7292-997d-11ac2d58d81e/s/'+id;
  return response(200,{url,expiresIn,expiresAt:new Date(expiresAt).toISOString()});
 }catch(e){
  console.error('quick-share operation failed',e.name,e.$metadata?.httpStatusCode);
  return response(502,{error:'Storage operation failed. Try again or check the function logs.'});
 }
};
