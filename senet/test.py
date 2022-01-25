import os
import subprocess
import getpass
import geopandas
import pyproj
import math

from datetime import datetime, timedelta

from get_creodias import get_data, prepare_data_senet_S2, eodata_path_creator
from sentinels import sentinel2, sentinel3
from timezone import get_offset
from core.leaf_spectra import leaf_spectra
from core.frac_green import fraction_green
from core.structural_params import str_parameters
from core.aerodynamic_roughness import aerodynamic_roughness
from core.warp_to_template import warp
from core.data_mining_sharpener import sharpen
from core.ecmwf_data_download import get
from core.ecmwf_data_preparation import prepare
from core.longwave_irradiance import longwave_irradiance
from core.net_shortwave_radiation import net_shortwave_radiation
from core.energy_fluxes import energy_fluxes
from core.daily_evapotranspiration import daily_evapotranspiration

# All ROI must be in WGS84
wgs_crs = pyproj.crs.CRS("epsg:4326")

USER = getpass.getuser()

meteo_datapath = "/home/eouser/uth/Cap_Bon/Meteo/"

AOI_path = "/home/eouser/uth/Cap_Bon/AOI/AOI_Cap_Bon.geojson"
AOI = geopandas.read_file(AOI_path)
CRS = AOI.crs

if CRS != wgs_crs:
    AOI = AOI.to_crs(wgs_crs.to_epsg())

WKT_GEOM = AOI.geometry[0]

user = "guest"
password = "guest"
start_date = "20210810"
end_date = "20210820"
data = get_data(AOI_path, start_date, end_date, user, password, producttype = "S2MSI2A")
data = prepare_data_senet_S2(data)
creodias_paths = eodata_path_creator(data)

# From all available images select the first
s2_path, s2_name = os.path.split(creodias_paths[0])
print(s2_path, s2_name)

s2 = sentinel2(s2_path, s2_name)
s2.getmetadata()

# Now select an available S3 image
start_date = s2.date
end_date = s2.date + timedelta(days=1)
data = get_data(AOI_path, start_date, end_date, user, password, platform = "Sentinel-3", producttype = "SL_2_LST___")
creodias_paths = eodata_path_creator(data)

for path in creodias_paths:
    # Again select the first image
    s3_path, s3_name = os.path.split(path)
    s3 = sentinel3(s3_path, s3_name)
    s3.getmetadata()

    if s3.date == s2.date:
        break

# Because the user has no permission to write make a new directory inside the user with the selected image name
home = "/home/eouser/uth"

if not os.path.exists(os.path.join(home, "Sentinel-2")):
    os.mkdir(os.path.join(home, "Sentinel-2"))
if not os.path.exists(os.path.join(home, "Sentinel-2", s2.tile_id)):
    os.mkdir(os.path.join(home, "Sentinel-2", s2.tile_id))
if not os.path.exists(os.path.join(home, "Sentinel-2", s2.tile_id, s2.name)):
    os.mkdir(os.path.join(home, "Sentinel-2", s2.tile_id, s2.name))

s2_savepath = os.path.join(home, "Sentinel-2", s2.tile_id)

if not os.path.exists(os.path.join(home, "Sentinel-3")):
    os.mkdir(os.path.join(home, "Sentinel-3"))
if not os.path.exists(os.path.join(home, "Sentinel-3", s3.name)):
    os.mkdir(os.path.join(home, "Sentinel-3", s3.name))

s3_savepath = os.path.join(home, "Sentinel-3") 

"""
# 1.SENTINEL 2 PREPROCESSING (GRAPH)
subprocess.run([f"/home/eouser/{USER}/esa-snap/bin/gpt", "./auxdata/sentinel_2_preprocessing.xml",
    "-PINPUT_S2_L2A={}".format(os.path.join(s2_path, s2_name, "MTD_MSIL2A.xml")),
    "-PAOI={}".format(WKT_GEOM),
    "-POUTPUT_REFL={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_REFL".format(s2.tile_id, s2.str_datetime))),
    "-POUTPUT_SUN_ZEN_ANG={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_SUN-ZEN-ANG".format(s2.tile_id, s2.str_datetime))),
    "-POUTPUT_MASK={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_MASK".format(s2.tile_id, s2.str_datetime))),
    "-POUTPUT_BIO={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_BIO".format(s2.tile_id, s2.str_datetime)))
    ])

# 2.ADD ELEVATION (GRAPH)
subprocess.run([f"/home/eouser/{USER}/esa-snap/bin/gpt", "./auxdata/add_elevation.xml",
    "-PINPUT_S2_MASK={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))),
    "-POUTPUT_SRTM_ELEV={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_ELEV".format(s2.tile_id, s2.str_datetime)))
    ])

# 3.ADD LANDCOVER (GRAPH)
subprocess.run([f"/home/eouser/{USER}/esa-snap/bin/gpt", "./auxdata/add_landcover.xml",
    "-PINPUT_S2_MASK={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_MASK.dim".format(s2.tile_id, s2.str_datetime))),
    "-POUTPUT_CCI_LC={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_LC".format(s2.tile_id, s2.str_datetime)))
    ])

# 4. Estimate leaf reflectance and transmittance
biophysical_file = os.path.join(s2_savepath, s2_name, "AUX_DATA", "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
output = os.path.join(s2_savepath, s2_name, "{}_{}_LEAF-REFL-TRAN.dim".format(s2.tile_id, s2.str_datetime))
leaf_spectra(biophysical_file, output)

# 5.Estimate fraction of green vegetation
sun_zenith_angle = os.path.join(s2_savepath, s2_name, "{}_{}_SUN-ZEN-ANG.dim".format(s2.tile_id, s2.str_datetime))
biophysical_file = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
output = os.path.join(s2_savepath, s2_name, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
minfc = 0.01
fraction_green(sun_zenith_angle, biophysical_file, minfc, output)

# 6.Maps of vegetation structural parameters
lcmap = os.path.join(s2_savepath, s2_name, "{}_{}_LC.dim".format(s2.tile_id, s2.str_datetime))
biophysical_file = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
fvg_map = os.path.join(s2_savepath, s2_name, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
landcover_band = "land_cover_CCILandCover-2015"
produce_vh = True
produce_fc = True
produce_chwr = True
produce_lw = True
produce_lid = True
produce_igbp = True
output = os.path.join(s2_savepath, s2_name, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
str_parameters(lcmap, biophysical_file, fvg_map, landcover_band,
    produce_vh, produce_fc, produce_chwr, produce_lw, produce_lid,
    produce_igbp, output)

# 7.Estimate aerodynamic roughness
biophysical_file = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
param_file = os.path.join(s2_savepath, s2_name, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
output = os.path.join(s2_savepath, s2_name, "{}_{}_AERO-ROUGH.dim".format(s2.tile_id, s2.str_datetime))
aerodynamic_roughness(biophysical_file, param_file, output)

# 8.S3 Pre-Processing (GRAPH)
subprocess.run([f"/home/{USER}/esa-snap/bin/gpt", "./auxdata/sentinel_3_preprocessing.xml",
    "-PINPUT_S3_L2={}".format(os.path.join(s3_path, s3_name)),
    "-PINPUT_AOI_WKT={}".format(WKT_GEOM),
    "-POUTPUT_observation_geometry={}".format(os.path.join(s3_savepath, s3_name, "LST_OBS-GEOM.dim")),
    "-POUTPUT_mask={}".format(os.path.join(s3_savepath, s3_name, "LST_MASK.dim")),
    "-POUTPUT_LST={}".format(os.path.join(s3_savepath, s3_name, "LST_data.dim"))
    ])


# 9.Warp to template
source_image = os.path.join(s3_savepath, s3_name, "LST_OBS-GEOM.dim")
temp_image = os.path.join(s2_savepath, s2_name, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))
output_image = os.path.join(s3_savepath, s3_name, "LST_OBS-GEOM-REPROJ.dim")
warp(source_image, temp_image, output_image)

# 10.Sharpen LST
s2_refl = os.path.join(s2_savepath, s2_name, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))
s3_lst = os.path.join(s3_savepath, s3_name, "LST_data.dim")
dem = os.path.join(s2_savepath, s2_name, "{}_{}_ELEV.dim".format(s2.tile_id, s2.str_datetime))
geom = os.path.join(s3_savepath, s3_name, "LST_OBS-GEOM-REPROJ.dim")
lst_mask = os.path.join(s3_savepath, s3_name, "LST_MASK.dim")
datetime_utc_str = s3.datetime.strftime("%Y-%m-%d %H:%M")
datetime_utc = datetime.strptime(datetime_utc_str, "%Y-%m-%d %H:%M")
output = os.path.join(s3_savepath, s3_name, "LST_SHARP.dim")
parallel_jobs = 3
moving_window_size = 30
sharpen(s2_refl, s3_lst, dem, geom, lst_mask, datetime_utc, output, moving_window_size = moving_window_size, parallel_jobs = parallel_jobs)

# 11. Download ERA5 reanalysis data
# N/W/S/E over a slightly larger area to contain all the AOI
N = math.ceil(AOI.bounds.maxy[0])
E = math.ceil(AOI.bounds.maxx[0])
W = math.floor(AOI.bounds.minx[0])
S = math.floor(AOI.bounds.miny[0])
CDS_AOI = "{}/{}/{}/{}".format(N, W, S, E)
start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
down_path = os.path.join(meteo_datapath, "meteo_{}_{}.nc".format(start_date, end_date))
get(CDS_AOI, start_date, end_date, down_path)

# 12.Prepare ERA5 reanalysis data
centroid = AOI.geometry[0].centroid
coordinates = {"lat": centroid.y, "lng": centroid.x, "date_time": s2.datetime}
offset = get_offset(**coordinates)
elevation_map = os.path.join(s2_savepath, s2_name, "{}_{}_ELEV.dim".format(s2.tile_id, s2.str_datetime))
ecmwf_data = os.path.join(meteo_datapath, "meteo_{}_{}.nc".format(start_date, end_date))
date_time_utc = s2.datetime
time_zone = offset
output = os.path.join(meteo_datapath, "meteo_{}_{}_PROC".format(start_date, end_date))
prepare(elevation_map, ecmwf_data, date_time_utc, time_zone, output)


# 13.Calculate Longwave irradiance
start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
meteo = os.path.join(meteo_datapath, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
output = os.path.join(meteo_datapath, "meteo_{}_LONG_IRRAD.dim".format(s2.date))
longwave_irradiance(meteo, output)

# 14. Calculate Net irradiance
start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
lsp_product = os.path.join(s2_savepath, s2_name, "{}_{}_LEAF-REFL-TRAN.dim".format(s2.tile_id, s2.str_datetime))
lai_product = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
csp_product = os.path.join(s2_savepath, s2_name, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
mi_product = os.path.join(meteo_datapath, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
sza_product =  os.path.join(s3_savepath, s3_name, "LST_OBS-GEON-REPROJ.dim")
output_file = os.path.join(s2_savepath, s2_name, "{}_{}_NET-RAD.dim".format(s2.tile_id, s2.str_datetime))
net_shortwave_radiation(lsp_product, lai_product, csp_product, mi_product, sza_product, output_file)

# 15. Estimate land surface energy fluxes
start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
lst = os.path.join(s3_savepath, s3_name, "LST_SHARP.dim")
lst_vza = os.path.join(s3_savepath, s3_name, "LST_OBS-GEON-REPROJ.dim")
lai = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
csp =  os.path.join(s2_savepath, s2_name, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
fgv = os.path.join(s2_savepath, s2_name, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
ar = os.path.join(s2_savepath, s2_name, "{}_{}_AERO-ROUGH.dim".format(s2.tile_id, s2.str_datetime))
mi = os.path.join(meteo_datapath, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
nsr = os.path.join(s2_savepath, s2_name, "{}_{}_NET-RAD.dim".format(s2.tile_id, s2.str_datetime))
li = os.path.join(meteo_datapath, "meteo_{}_LONG_IRRAD.dim".format(s2.date))
mask = os.path.join(s2_savepath, s2_name, "{}_{}_MASK.dim".format(s2.tile_id, s2.str_datetime))
output_file = os.path.join(s2_savepath, s2_name, "{}_{}_EN-FLUX.dim".format(s2.tile_id, s2.str_datetime))
energy_fluxes(lst, lst_vza, lai, csp, fgv, ar, mi, nsr, li, mask, output_file)


start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
ief_file = os.path.join(s2_savepath, s2_name, "{}_{}_EN-FLUX.dim".format(s2.tile_id, s2.str_datetime))
mi_file = os.path.join(meteo_datapath, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
output_file = os.path.join(s2_savepath, s2_name, "{}_{}_EVAP.dim".format(s2.tile_id, s2.str_datetime))

daily_evapotranspiration(ief_file, mi_file, output_file)
"""