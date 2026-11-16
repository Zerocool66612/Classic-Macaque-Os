"""One-login recovery request; no saved preferences are changed."""
import os
from pathlib import Path
def marker(folder=None):return (Path(folder) if folder else Path.home()/'.local/state/macaque')/'safe-next-login'
def schedule(enabled=True,folder=None):
 p=marker(folder)
 if enabled:p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Recovery requested for the next login.\n');p.chmod(0o600)
 else:p.unlink(missing_ok=True)
def consume(env,folder=None):
 p=marker(folder);safe=env.get('MACAQUE_SAFE_SESSION')=='1'
 if p.is_file():p.unlink();safe=True
 if safe:env['MACAQUE_SAFE_SESSION']='1'
 return safe
