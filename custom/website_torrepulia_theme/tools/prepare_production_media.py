"""Convert the three owner-provided process photographs; no retouching or crop."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageOps

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path)
args=parser.parse_args()
destination=Path(__file__).resolve().parents[1]/'static/src/cinematic/owner'
files={'bin_forati.jpeg':'process-crates.webp','molitura.jpeg':'process-mill.webp',
       'confezionamento_frantoio.jpeg':'process-bottling.webp'}
for source,target in files.items():
    with Image.open(args.source/source) as original:
        photo=ImageOps.exif_transpose(original).convert('RGB')
        photo.thumbnail((960,960),Image.Resampling.LANCZOS)
        path=destination/target
        photo.save(path,'WEBP',quality=88,method=6)
        print(json.dumps({'file':target,'width':photo.width,'height':photo.height,'bytes':path.stat().st_size}))
