"""Linux power-supply readings and NetworkManager's escaped table format."""
from pathlib import Path

def split_fields(line):
    fields=[];part='';escaped=False
    for c in line:
        if escaped:part+=c;escaped=False
        elif c=='\\':escaped=True
        elif c==':':fields.append(part);part=''
        else:part+=c
    if escaped:part+='\\'
    return fields+[part]

def batteries(root='/sys/class/power_supply'):
    result=[]
    def read(p,name):
        try:return (p/name).read_text().strip()
        except OSError:return ''
    for p in sorted(Path(root).glob('*')):
        if read(p,'type')!='Battery' or read(p,'present')=='0':continue
        # Ignore mice/headsets; report the computer's batteries.
        if read(p,'scope')=='Device':continue
        try:capacity=max(0,min(100,int(read(p,'capacity'))))
        except ValueError:capacity=None
        result.append({'name':p.name,'percent':capacity,'status':read(p,'status') or 'Unknown'})
    return result

def battery_summary(items):
    if not items:return '', 'No laptop battery detected'
    # Show each pack separately instead of inventing a combined percentage.
    text=' / '.join(('?' if b['percent'] is None else str(b['percent']))+'%' for b in items)
    charging=any(b['status']=='Charging' for b in items)
    return ('+ ' if charging else 'Bat ')+text, '\n'.join(f"{b['name']}: {b['percent'] if b['percent'] is not None else '?'}% · {b['status']}" for b in items)
