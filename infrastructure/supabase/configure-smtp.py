#!/usr/bin/env python3
"""Use HomeLab Google.smtp for Supabase SMTP, without secret output."""
from email.message import EmailMessage
import json
from pathlib import Path
import smtplib
import ssl
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
def run(args,data=None):
    result=subprocess.run(args,input=data,text=True,capture_output=True)
    assert result.returncode==0,'Private operation failed; output withheld'
    return result.stdout
def get(name):return json.loads(run([str(root/'scripts/op-sa'),'item','get',name,'--vault','HomeLab','--format','json']))
google=get('Google')
password=next(field['value'] for field in google['fields'] if field.get('label','').lower()=='smtp').replace(' ','')
assert len(password)==16,'Expected a Google app password in concealed smtp field'
user='l3bctl@gmail.com'
with smtplib.SMTP('smtp.gmail.com',587,timeout=20) as client:
    client.ehlo();client.starttls(context=ssl.create_default_context());client.ehlo()
    client.login(user,password)
    if '--send-test' in sys.argv:
        message=EmailMessage()
        message['From']='Anurag Vishwakarma (l3b) <'+user+'>'
        message['To']=user
        message['Subject']='Homelab SMTP validation'
        message.set_content('Gmail STARTTLS authentication and submission succeeded for the Kubernetes Supabase migration. No credentials are included in this message.')
        client.send_message(message)
canonical=get('Supabase')
for field in canonical['fields']:
    if field.get('label')=='deployment-secrets':
        values=json.loads(field['value']);values.update(smtpUsername=user,smtpPassword=password);field['value']=json.dumps(values)
run([str(root/'scripts/op-sa'),'item','edit',canonical['id'],'--vault','HomeLab','--format','json','-'],json.dumps(canonical))
secret={'apiVersion':'v1','kind':'Secret','metadata':{'name':'supabase-prod-smtp','namespace':'supabase-prod'},'stringData':{'username':user,'password':password}}
run(['kubectl','--context','k8s','apply','-f','-'],json.dumps(secret))
print('PASS: Gmail STARTTLS login; Supabase SMTP Secret and canonical vault record updated'+('; test message submitted to homelab mailbox' if '--send-test' in sys.argv else ''))
