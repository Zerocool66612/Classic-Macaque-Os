"""Desktop-only compositor rules: dialogs sharing the Qt app_id stay normal-sized."""
import fnmatch,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent.parent
config=ET.parse(root/'desktop/labwc-rc.xml')
rules=config.findall('./windowRules/windowRule')
def matches(rule,identifier,title):
 return all(fnmatch.fnmatchcase(value.lower(),rule.get(key,'*').lower()) for key,value in [('identifier',identifier),('title',title)])
def actions(identifier,title):
 return [a.get('name') for rule in rules if matches(rule,identifier,title) for a in rule.findall('action')]
for version in ['0.41','0.41.1','1.0']:
 names=actions('org.macaque.Classic','Macaque Classic '+version+' — Macaque Desktop')
 assert 'Maximize' in names and 'ToggleAlwaysOnBottom' in names
for title in ['Restart','Shut Down','Log Out','Macaque session','Save Web Download','Settings','Macaque Classic Update']:
 names=actions('org.macaque.Classic',title)
 assert 'Maximize' not in names and 'ToggleAlwaysOnBottom' not in names,title
assert actions('another.application','Macaque Classic 0.41 — Macaque Desktop')==[]
print('PASS: only the Macaque desktop matches the maximize/bottom rule; shared-app-id dialogs do not.')
