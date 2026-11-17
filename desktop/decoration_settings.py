"""Independent window-button style/side, shared with the Wayland compositor."""
import json,os,subprocess
from pathlib import Path
STYLES=('Classic','Traffic lights')
SIDES=('Left','Right')
def controls(state):
    style=state.get('window_buttons','Classic')
    # Retain the previous Classic appearance while removing font/theme coupling.
    if style not in STYLES:style='Classic'
    side=state.get('window_button_side','Left')
    if side not in SIDES:side='Left'
    return {'window_buttons':style,'window_button_side':side}
def saved():
    from input_settings import folder
    try:return controls(json.loads((folder()/'window-controls.json').read_text()))
    except (OSError,ValueError,TypeError,AttributeError):return controls({})
def decorate(root):
    state=saved();theme=root.find('theme')
    import xml.etree.ElementTree as ET
    if theme is None:theme=ET.SubElement(root,'theme')
    def node(parent,name):
        found=parent.find(name)
        return found if found is not None else ET.SubElement(parent,name)
    node(theme,'name').text='Macaque Platinum' if state['window_buttons']=='Classic' else 'Macaque Traffic'
    node(node(theme,'titlebar'),'layout').text='close,iconify,max,shade:menu' if state['window_button_side']=='Left' else 'menu:iconify,max,shade,close'
def sync(state):
    if os.environ.get('MACAQUE_WAYLAND_SESSION')!='1' or os.environ.get('MACAQUE_PREVIEW_SESSION')=='1':return
    from input_settings import folder,atomic,render
    state=controls(state);path=folder()/'window-controls.json'
    if path.exists() and saved()==state:return
    atomic(path,json.dumps(state));render()
    subprocess.run(['labwc','--reconfigure'],check=True,capture_output=True,timeout=3)
