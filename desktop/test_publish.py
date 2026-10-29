import os,tempfile,subprocess,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);source=p/'source';source.mkdir();shutil.copy2(root/'publish-github.sh',source/'publish-github.sh');bin=p/'bin';bin.mkdir();calls=p/'calls'
 fake=bin/'git';fake.write_text('''#!/usr/bin/env python3
import sys,os
from pathlib import Path
args=sys.argv[1:]
with open(os.environ['TEST_GIT_CALLS'],'a') as f:f.write(' '.join(args)+'\\n')
if args[0]=='ls-remote':
 if os.environ.get('TEST_NONEMPTY'):print('abc refs/heads/main')
 sys.exit(0)
if args[0]=='config':print('Test Author');sys.exit(0)
if args[0]=='remote' and args[1]=='get-url':sys.exit(1)
if args[0]=='diff':sys.exit(1)
if args[0]=='init':Path('.git').mkdir(exist_ok=True)
''');fake.chmod(0o755);env=dict(os.environ,PATH=str(bin)+os.pathsep+os.environ['PATH'],TEST_GIT_CALLS=str(calls))
 def run(url,extra=None):return subprocess.run(['bash',str(source/'publish-github.sh'),url],env=dict(env,**(extra or {})),capture_output=True,text=True)
 result=run('https://github.com/example/macaque-classic.git',{'TEST_NONEMPTY':'1'});assert result.returncode and not (source/'.git').exists();assert 'push' not in calls.read_text()
 calls.unlink();result=run('https://github.com/example/macaque-classic.git');assert result.returncode==0,result.stderr;log=calls.read_text();assert 'push --set-upstream origin HEAD:main' in log and '--force' not in log
 calls.unlink();result=run('https://github.com/example/repo;touch /tmp/not-authorized');assert result.returncode and not calls.exists()
print('PASS: publish helper refuses nonempty remotes and invalid URLs; simulated empty-remote publish uses no force-push. No actual remote was modified.')
