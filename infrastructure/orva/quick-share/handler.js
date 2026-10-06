const crypto = require('node:crypto');
const path = require('node:path');
const {kv} = require('orva');
const {S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand} = require('@aws-sdk/client-s3');
const {getSignedUrl} = require('@aws-sdk/s3-request-presigner');
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

const HTML = "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\"><title>Quick Share</title><style>:root{color-scheme:light dark;--bg:#f7f7f5;--card:#fff;--text:#171717;--muted:#777;--line:#d8d8d3;--soft:#f0f0ed}@media(prefers-color-scheme:dark){:root{--bg:#111;--card:#171717;--text:#f3f3f1;--muted:#92928d;--line:#343430;--soft:#222220}}*{box-sizing:border-box}html,body{margin:0;min-height:100%;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif;background:var(--bg);color:var(--text)}body{min-height:100vh;display:grid;place-items:center;padding:18px}main{width:min(100%,440px)}.drop{min-height:205px;background:var(--card);border:1.5px dashed var(--line);border-radius:18px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:28px;cursor:pointer;transition:.15s ease}.drop:hover,.drop.drag{border-color:var(--text);transform:translateY(-1px)}.icon{width:42px;height:42px;border-radius:12px;background:var(--soft);display:grid;place-items:center;font-size:22px;margin-bottom:16px}.title{font-size:15px;font-weight:650}.sub{font-size:13px;color:var(--muted);margin-top:7px}input[type=file]{display:none}.status{display:none;margin-top:12px;padding:14px;background:var(--card);border:1px solid var(--line);border-radius:14px}.name{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.detail{font-size:12px;color:var(--muted);margin-top:4px}.progress{height:3px;background:var(--soft);border-radius:999px;overflow:hidden;margin-top:12px}.bar{height:100%;width:0;background:var(--text);transition:width .12s ease}.result{display:none;gap:8px;margin-top:12px}.url{min-width:0;flex:1;border:1px solid var(--line);background:var(--card);color:var(--text);border-radius:12px;padding:12px 13px;font-size:13px;outline:none}button{border:0;border-radius:12px;padding:0 16px;background:var(--text);color:var(--bg);font-weight:650;cursor:pointer}.error{display:none;color:#d44;font-size:13px;text-align:center;margin-top:10px}@media(max-width:480px){.drop{min-height:190px}.result{flex-direction:column}.result button{height:44px}.url{width:100%}}.expiry{display:flex;align-items:center;justify-content:space-between;margin:18px 0;font-size:16px}.expiry select{font:inherit;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--text)}:focus-visible{outline:2px solid var(--text);outline-offset:3px}.url{font-size:16px}input[type=file]{display:block;width:100%;margin-top:16px;font-size:14px}</style></head><body><main><label class=\"drop\" id=\"drop\" for=\"file\"><div class=\"icon\">↑</div><div class=\"title\">Drop a file or choose one</div><div class=\"sub\">Images & documents · max 4 MiB</div><input id=\"file\" type=\"file\" accept=\"image/*,.pdf,.txt,.md,.csv,.json,.xml,.rtf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp\"></label><label class=\"expiry\" for=\"expiry\">Expires after <select id=\"expiry\"><option value=\"3600\">1 hour</option><option value=\"21600\">6 hours</option><option value=\"86400\">1 day</option><option value=\"259200\">3 days</option><option value=\"604800\">7 days</option></select></label><section aria-live=\"polite\" class=\"status\" id=\"status\"><div class=\"name\" id=\"name\"></div><div class=\"detail\" id=\"detail\">Preparing…</div><div class=\"progress\"><div class=\"bar\" id=\"bar\"></div></div></section><div class=\"result\" id=\"result\"><input class=\"url\" id=\"url\" readonly><button id=\"copy\" type=\"button\">Copy</button></div><div role=\"alert\" class=\"error\" id=\"error\"></div></main><script>const MAX=4*1024*1024,$=id=>document.getElementById(id),input=$(\"file\"),drop=$(\"drop\"),statusEl=$(\"status\"),nameEl=$(\"name\"),detail=$(\"detail\"),bar=$(\"bar\"),result=$(\"result\"),urlEl=$(\"url\"),copy=$(\"copy\"),errorEl=$(\"error\");function human(n){return n<1024?n+\" B\":n<1048576?(n/1024).toFixed(1)+\" KB\":(n/1048576).toFixed(1)+\" MB\"}function fail(m){errorEl.textContent=m;errorEl.style.display=\"block\";detail.textContent=\"Upload failed\";bar.style.width=\"0%\"}function reset(){errorEl.style.display=\"none\";result.style.display=\"none\";bar.style.width=\"0%\";copy.textContent=\"Copy\"}\nlet busy=false;\nasync function upload(file){\n if(busy)return;reset();if(!file)return;\n if(file.size<1)return fail(\"The file is empty.\");\n if(file.size>MAX)return fail(\"File must be 4 MiB or smaller.\");\n busy=true;input.disabled=true;$(\"expiry\").disabled=true;\n statusEl.style.display=\"block\";nameEl.textContent=file.name;\n try{\n  detail.textContent=human(file.size)+\" · preparing\";\n  const data=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(\",\")[1]);r.onerror=()=>reject(new Error(\"Could not read the file.\"));r.readAsDataURL(file)});\n  const b=await new Promise((resolve,reject)=>{\n   const x=new XMLHttpRequest();x.open(\"POST\",location.href,true);x.timeout=45000;x.setRequestHeader(\"Content-Type\",\"application/json\");\n   x.upload.onprogress=e=>{if(e.lengthComputable)bar.style.width=Math.round(e.loaded/e.total*90)+\"%\"};\n   x.onload=()=>{let b;try{b=JSON.parse(x.responseText)}catch{return reject(new Error(\"Server returned an invalid response.\"))}\n    if(x.status>=200&&x.status<300)resolve(b);else reject(new Error(b.error||(\"Request failed (\"+x.status+\"). Choose the file again to retry.\")))};\n   x.onerror=()=>reject(new Error(\"Network error. Choose the file again to retry.\"));\n   x.ontimeout=()=>reject(new Error(\"Upload timed out. Choose the file again to retry.\"));\n   detail.textContent=human(file.size)+\" · uploading\";\n   x.send(JSON.stringify({name:file.name,type:file.type,size:file.size,expiresIn:Number($(\"expiry\").value),data}));\n  });\n  bar.style.width=\"100%\";detail.textContent=\"Uploaded · expires \"+new Date(b.expiresAt).toLocaleString();\n  urlEl.value=b.url;result.style.display=\"flex\";\n }catch(e){fail(e.message||\"Upload failed. Choose the file again to retry.\")}\n finally{busy=false;input.disabled=false;$(\"expiry\").disabled=false;input.value=\"\"}\n}\ninput.addEventListener(\"change\",()=>upload(input.files[0]));[\"dragenter\",\"dragover\"].forEach(v=>drop.addEventListener(v,e=>{e.preventDefault();drop.classList.add(\"drag\")}));[\"dragleave\",\"drop\"].forEach(v=>drop.addEventListener(v,e=>{e.preventDefault();drop.classList.remove(\"drag\")}));drop.addEventListener(\"drop\",e=>upload(e.dataTransfer.files[0]));copy.addEventListener(\"click\",async()=>{try{await navigator.clipboard.writeText(urlEl.value);copy.textContent=\"Copied\";setTimeout(()=>copy.textContent=\"Copy\",1200)}catch{urlEl.select();document.execCommand(\"copy\")}});</script></body></html>";

exports.handler=async(event)=>{
 const method=String(event.method||'GET').toUpperCase();
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
  const id=crypto.randomBytes(24).toString('hex'),ext=path.extname(name).toLowerCase();
  const key='quick-share/'+id+(/^\.[a-z0-9]{1,10}$/.test(ext)?ext:'');
  const expiresAt=Date.now()+expiresIn*1000;
  await kv.put('share:'+id,{key,expiresAt},{ttlSeconds:0});
  await send(s,new PutObjectCommand({Bucket:s.Bucket,Key:key,Body:bytes,ContentType:type}));
  const url=await getSignedUrl(s.client,new GetObjectCommand({Bucket:s.Bucket,Key:key}),{expiresIn});
  return response(200,{url,expiresIn,expiresAt:new Date(expiresAt).toISOString()});
 }catch(e){
  console.error('quick-share operation failed',e.name,e.$metadata?.httpStatusCode);
  return response(502,{error:'Storage operation failed. Try again or check the function logs.'});
 }
};
