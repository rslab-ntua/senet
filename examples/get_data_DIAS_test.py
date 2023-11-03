from creodias_finder import query
from datetime import datetime, timedelta
import geopandas
import pyproj
from senet.sentinels import sentinel2, sentinel3
import os

def get_data_DIAS(area:str, start_date:str, end_date:str, platform:str = "Sentinel2", **kwargs):
    """Query the Copernicus Data Space Ecosystem (CDSE) OpenSearch service for available products.
    - For Sentinel-2 catalog attributes: https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/describe.xml
    - For Sentinel-3 catalog attributes: https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel3/describe.xml
    Args:
        area (str): WKT geometry of the AOI.
        start_date (str): Start date in YYYYMMDD format.
        end_date (str): Start date in YYYYMMDD format.
        platform (str, optional): Platform name (like Sentinel2 or Sentinel3). Defaults to "Sentinel2".

    Returns:
        list: List of available products in CreoDIAS based on the query.
    """
    data = []
    results = query.query(
        platform,
        geometry=area,
        start_date=datetime(int(start_date[:4]), int(start_date[4:6]), int(start_date[6:])),
        end_date=datetime(int(end_date[:4]), int(end_date[4:6]), int(end_date[6:])),
        **kwargs)
    for key in results:
        data.append(results[key]["properties"]["productIdentifier"])

    return data

AOI_path = "/home/eouser/uth/Benchmarking_Senet/Geometries/ROI.geojson"
AOI = geopandas.read_file(AOI_path)
CRS = AOI.crs
wgs_crs = pyproj.crs.CRS("epsg:4326")

if CRS != wgs_crs:
    AOI = AOI.to_crs(wgs_crs.to_epsg())

WKT_GEOM = AOI.geometry[0]
start_date = "20180410"
end_date = "20180420"
creodias_paths = get_data_DIAS(WKT_GEOM, start_date, end_date, productType = "S2MSI2A")

sentinel_2_data = []
for path in creodias_paths:
    s2_path, s2_name = os.path.split(path)
    s2 = sentinel2(s2_path, s2_name)
    s2.getmetadata()
    sentinel_2_data.append(s2)

print(f"All Sentinel 2 images: {sentinel_2_data}")
print(f"Starting processing for all images...")

for s2 in sentinel_2_data:  
    print(f"----PAIR----")
    print(f"Sentinel 2 image: {s2.name}")

    start_date = s2.date
    end_date = s2.date + timedelta(days = 1)
    creodias_paths = get_data_DIAS(WKT_GEOM, start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"), platform = "Sentinel3", productType = "SL_2_LST___")
    print(creodias_paths)
    # From all S3 images select the one with the least cloud coverage at the same date with Sentinel-2 data
    candidates = []
    for path in creodias_paths:
        s3_path, s3_name = os.path.split(path)
        s3 = sentinel3(s3_path, s3_name)
        s3.getmetadata()

        if s3.date == s2.date:
            candidates.append(s3)

        s3_dates = [image.datetime for image in candidates]
        selected_datetime = min(s3_dates, key = lambda d: abs(d - s2.datetime))
        index = s3_dates.index(selected_datetime)
        s3 = candidates[index]
