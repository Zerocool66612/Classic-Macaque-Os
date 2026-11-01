#!/usr/bin/python3
"""GitHub release metadata/checksummed desktop downloads; no install privilege."""
import hashlib,json,re,sys,urllib.request,urllib.parse,os
from pathlib import Path
from maintenance import metadata,digest
API='https://api.github.com/repos/Zerocool66612/Classic-Macaque-Os/releases'
PREFIX='https://github.com/Zerocool66612/Classic-Macaque-Os/releases/download/'
class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        u=urllib.parse.urlsplit(newurl)
        if u.scheme!='https' or not (u.hostname=='github.com' or (u.hostname or '').endswith('.githubusercontent.com')):raise ValueError('Unexpected download redirect.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def read_url(url,limit):
    req=urllib.request.Request(url,headers={'User-Agent':'Macaque-Classic-Updater','Accept':'application/vnd.github+json' if url==API else '*/*'})
    with urllib.request.build_opener(HTTPSRedirect()).open(req,timeout=30) as response:
        content=response.read(limit+1)
        if len(content)>limit:raise ValueError('Download exceeds the allowed size.')
        return content

def releases(data):
    result=[]
    for release in data:
        if release.get('draft'):continue
        assets={x['name']:x for x in release.get('assets',[]) if isinstance(x.get('name'),str)}
        for name,asset in assets.items():
            if not re.fullmatch(r'macaque-classic_[0-9][A-Za-z0-9.+~\-]*_amd64\.deb',name) or name+'.sha256' not in assets:continue
            url=asset.get('browser_download_url','');checksum=assets[name+'.sha256'].get('browser_download_url','')
            if not url.startswith(PREFIX) or not checksum.startswith(PREFIX):continue
            result.append({'name':name,'version':name.split('_')[1],'url':url,'checksum_url':checksum,'tag':release['tag_name'],'prerelease':bool(release.get('prerelease'))})
    return result

def download(item,folder):
    if not item.get('url','').startswith(PREFIX) or not item.get('checksum_url','').startswith(PREFIX):raise ValueError('This is not a Macaque release asset.')
    name=item['name']
    if not re.fullmatch(r'macaque-classic_[0-9][A-Za-z0-9.+~\-]*_amd64\.deb',name):raise ValueError('Invalid desktop package name.')
    checksum=read_url(item['checksum_url'],8192).decode().strip().split()
    if len(checksum)!=2 or checksum[1].lstrip('*')!=name or not re.fullmatch('[0-9a-fA-F]{64}',checksum[0]):raise ValueError('Invalid release checksum file.')
    content=read_url(item['url'],50*1024*1024)
    if hashlib.sha256(content).hexdigest()!=checksum[0].lower():raise ValueError('Desktop package checksum did not match.')
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);target=folder/name
    # Do not overwrite a user's existing download.
    if target.exists():target=folder/(target.stem+'-'+os.urandom(4).hex()+'.deb')
    created=False
    try:
        with target.open('xb') as f:created=True;f.write(content)
        info=metadata(target)
    except Exception:
        if created:target.unlink(missing_ok=True)
        raise
    return {**info,'path':str(target.resolve()),'sha256':digest(target)}
if __name__=='__main__':
    try:
        p=json.loads(sys.stdin.read(32768));action=p['action']
        if action=='check':result={'releases':releases(json.loads(read_url(API,2*1024*1024)))}
        elif action=='download':result=download(p['release'],p['folder'])
        elif action=='inspect':result={**metadata(p['path']),'path':str(Path(p['path']).resolve()),'sha256':digest(p['path'])}
        else:raise ValueError('Unknown update action.')
        print(json.dumps(result))
    except Exception as ex:print('Update request failed: '+str(ex),file=sys.stderr);sys.exit(1)
