import json, hashlib, os, sys
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from pystac_client import Client
OUT=sys.argv[1]
c=Client.open("https://earth-search.aws.element84.com/v1")
ids=["S2A_19HED_20241105_0_L2A","S2B_19HED_20260104_0_L2A","S2C_19HED_20260926_0_L2A",
     "S2C_19HED_20261006_0_L2A","S2B_19HED_20261031_0_L2A","S2C_19HED_20261105_0_L2A"]
bbox=[-68.95,-33.16,-68.85,-33.08]
assets=["red","nir","nir08","swir16","scl","visual"]
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"]="EMPTY_DIR"
meta={}
for it in c.search(collections=["sentinel-2-l2a"],ids=ids).items():
    d=it.datetime.strftime("%Y%m%d"); meta[d]={"id":it.id,"properties":it.properties,"assets":{}}
    for a in assets:
        href=it.assets[a].href
        with rasterio.open(href) as src:
            b=transform_bounds("EPSG:4326",src.crs,*bbox)
            w=from_bounds(*b,transform=src.transform).round_offsets().round_lengths()
            arr=src.read(window=w); prof=src.profile.copy()
            prof.update(width=arr.shape[2],height=arr.shape[1],transform=src.window_transform(w),driver="GTiff",compress="deflate",tiled=False)
            prof.pop("blockxsize",None); prof.pop("blockysize",None)
            fn=os.path.join(OUT,f"{d}_{a}.tif")
            with rasterio.open(fn,"w",**prof) as dst: dst.write(arr)
        h=hashlib.sha256(open(fn,"rb").read()).hexdigest()
        meta[d]["assets"][a]={"href":href,"file":os.path.basename(fn),"sha256":h,"shape":list(arr.shape),"res":src.res}
        print(d,a,arr.shape,src.res,flush=True)
json.dump(meta,open(os.path.join(OUT,"stac_metadata.json"),"w"),indent=1,default=str)
