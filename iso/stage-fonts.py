"""Stage the unmodified, MIT-licensed Chicago Kare font and attribution."""
from pathlib import Path
import shutil
SOURCE=Path(__file__).resolve().parent.parent/'desktop/fonts/chicago-kare'
def stage(root):
    root=Path(root)
    for source,destination in [(SOURCE/'ChicagoKare-Regular.ttf',root/'usr/share/fonts/truetype/macaque/ChicagoKare-Regular.ttf'),(SOURCE/'LICENSE',root/'usr/share/doc/macaque-classic/fonts/chicago-kare/LICENSE')]:
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
        destination.chmod(0o644)
if __name__=='__main__':
    import sys
    stage(sys.argv[1])
