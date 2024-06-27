import os
import shutil
import subprocess
import getpass
import geopandas
import pyproj
import math
import gc
from datetime import datetime, timedelta

from senet.get_creodias import get_data_DIAS
from senet.sentinels import sentinel2, sentinel3
from senet.timezone import get_offset
from senet.core.graphs import s2_preprocessing, elevation, landcover, s3_preprocessing
from senet.core.leaf_spectra import leaf_spectra
from senet.core.frac_green import fraction_green
from senet.core.structural_params import str_parameters
from senet.core.aerodynamic_roughness import aerodynamic_roughness
from senet.core.warp_to_template import warp
from senet.core.data_mining_sharpener import sharpen
from senet.core.ecmwf_data_download import get
from senet.core.ecmwf_data_preparation import prepare
from senet.core.longwave_irradiance import longwave_irradiance
from senet.core.net_shortwave_radiation import net_shortwave_radiation
from senet.core.energy_fluxes import energy_fluxes
from senet.core.daily_evapotranspiration import daily_evapotranspiration

# All ROI must be in WGS84
WGS_CRS = pyproj.crs.CRS("epsg:4326")

USER = getpass.getuser()

PROJECT_FOLDER = "/home/eouser/uth/cb-monthly/"
if not os.path.exists(PROJECT_FOLDER):
    os.makedirs(PROJECT_FOLDER)

METEO_DATAPATH = os.path.join(PROJECT_FOLDER, "Meteorological_Data/")
if not os.path.exists(METEO_DATAPATH):
    os.makedirs(METEO_DATAPATH)

SENTINEL_2_DATAPATH = os.path.join(PROJECT_FOLDER, "Sentinel-2/")
if not os.path.exists(SENTINEL_2_DATAPATH):
    os.makedirs(SENTINEL_2_DATAPATH)

SENTINEL_3_DATAPATH = os.path.join(PROJECT_FOLDER, "Sentinel-3/")
if not os.path.exists(SENTINEL_3_DATAPATH):
    os.makedirs(SENTINEL_3_DATAPATH)

AOI_PATH = "/home/eouser/uth/cb-monthly/Geometries/AOI.geojson"
AOI = geopandas.read_file(AOI_PATH)
CRS = AOI.crs

if CRS != WGS_CRS:
    AOI = AOI.to_crs(WGS_CRS.to_epsg())

WKT_GEOM = AOI.geometry[0]

# Currently we use an ESA SCIHUB account for querying for data and we create the CreoDIAS paths. We can probably use CreoDIAS FinderAPI later on.
start_date = "20180101"
end_date = "20230101"

creodias_paths = get_data_DIAS(WKT_GEOM, start_date, end_date, productType = "S2MSI2A", tileId = "32SPF", relativeOrbitNumber = "122", cloudCover = "[0, 80]")

# From all available images select the one with the least cloud coverage
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
    print(f"Sentinel 2 image: {os.path.join(s2.path, s2.name)}")
    S2_SAVEPATH = os.path.join(SENTINEL_2_DATAPATH, s2.tile_id, s2.name) 
    if os.path.exists(S2_SAVEPATH):
        print("Already exists...")
    else:
        if not os.path.exists(os.path.join(SENTINEL_2_DATAPATH, s2.tile_id, s2.name)):
            os.makedirs(os.path.join(SENTINEL_2_DATAPATH, s2.tile_id, s2.name))
        # Now select an available S3 image
        start_date = s2.date
        end_date = s2.date + timedelta(days = 1)
        creodias_paths = get_data_DIAS(WKT_GEOM, start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"), platform = "Sentinel3", productType = "SL_2_LST___")

        # From all S3 images select the one with the least cloud coverage at the same date with Sentinel-2 data
        candidates = []
        for path in creodias_paths:
            s3_path, s3_name = os.path.split(path)
            s3 = sentinel3(s3_path, s3_name)
            s3.getmetadata()

            if s3.date == s2.date:
                candidates.append(s3)
        
        if len(candidates) == 0:
            print (f"No available S3 candidates found for {s2.name}")
            print(f"Will search for the next available date.")
            start_date = s2.date - timedelta(days=1)
            end_date = s2.date + timedelta(days=2)
            creodias_paths = get_data_DIAS(WKT_GEOM, start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"), platform = "Sentinel3", productType = "SL_2_LST___")
            for path in creodias_paths:
                s3_path, s3_name = os.path.split(path)
                s3 = sentinel3(s3_path, s3_name)
                s3.getmetadata()
                candidates.append(s3)
                    
        s3_dates = [image.datetime for image in candidates]
        selected_datetime = min(s3_dates, key = lambda d: abs(d - s2.datetime))
        index = s3_dates.index(selected_datetime)
        s3 = candidates[index]
        
        if not os.path.exists(os.path.join(SENTINEL_3_DATAPATH, s3.name)):
            os.makedirs(os.path.join(SENTINEL_3_DATAPATH, s3.name))
        S3_SAVEPATH = os.path.join(SENTINEL_3_DATAPATH, s3.name) 
        
        print(f"Sentinel 3 image: {os.path.join(s3.path, s3.name)}")
        print(f"------------")
        print(f"Starting processing pair...")

        # 1.SENTINEL 2 PREPROCESSING (GRAPH)
        gpt = f"/home/eouser/{USER}/esa-snap/bin/gpt"
        S2_L2A = os.path.join(s2.path, s2.name, "MTD_MSIL2A.xml")
        aoi = WKT_GEOM
        out_refl = os.path.join(S2_SAVEPATH, "{}_{}_REFL".format(s2.tile_id, s2.str_datetime))
        out_sun_zenith = os.path.join(S2_SAVEPATH, "{}_{}_SUN-ZEN-ANG".format(s2.tile_id, s2.str_datetime))
        out_mask = os.path.join(S2_SAVEPATH, "{}_{}_MASK".format(s2.tile_id, s2.str_datetime))
        out_bio = os.path.join(S2_SAVEPATH, "{}_{}_BIO".format(s2.tile_id, s2.str_datetime))
        s2_preprocessing(gpt, S2_L2A, aoi, out_refl, out_sun_zenith, out_mask, out_bio)

        # 2.ADD ELEVATION (GRAPH)
        gpt = f"/home/eouser/{USER}/esa-snap/bin/gpt"
        in_mask = os.path.join(S2_SAVEPATH, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))
        out_elev = os.path.join(S2_SAVEPATH, "{}_{}_ELEV".format(s2.tile_id, s2.str_datetime))
        elevation(gpt, in_mask, out_elev)
        
        # 3.ADD LANDCOVER (GRAPH)
        gpt = f"/home/eouser/{USER}/esa-snap/bin/gpt"
        in_mask = os.path.join(S2_SAVEPATH, "{}_{}_MASK.dim".format(s2.tile_id, s2.str_datetime))
        out_lc = os.path.join(S2_SAVEPATH, "{}_{}_LC".format(s2.tile_id, s2.str_datetime))
        landcover(gpt, in_mask, out_lc)
        
        # 4. Estimate leaf reflectance and transmittance
        biophysical_file = os.path.join(S2_SAVEPATH, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
        output = os.path.join(S2_SAVEPATH, "{}_{}_LEAF-REFL-TRAN.dim".format(s2.tile_id, s2.str_datetime))
        leaf_spectra(biophysical_file, output)

        # 5.Estimate fraction of green vegetation
        sun_zenith_angle = os.path.join(S2_SAVEPATH, "{}_{}_SUN-ZEN-ANG.dim".format(s2.tile_id, s2.str_datetime))
        biophysical_file = os.path.join(S2_SAVEPATH, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
        output = os.path.join(S2_SAVEPATH, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
        minfc = 0.01
        fraction_green(sun_zenith_angle, biophysical_file, minfc, output)

        # 6.Maps of vegetation structural parameters
        lcmap = os.path.join(S2_SAVEPATH, "{}_{}_LC.dim".format(s2.tile_id, s2.str_datetime))
        biophysical_file = os.path.join(S2_SAVEPATH, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
        fvg_map = os.path.join(S2_SAVEPATH, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
        landcover_band = "land_cover_CCILandCover-2015"
        produce_vh = True
        produce_fc = True
        produce_chwr = True
        produce_lw = True
        produce_lid = True
        produce_igbp = True
        output = os.path.join(S2_SAVEPATH, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
        str_parameters(lcmap, biophysical_file, fvg_map, landcover_band,
            produce_vh, produce_fc, produce_chwr, produce_lw, produce_lid,
            produce_igbp, output)

        # 7.Estimate aerodynamic roughness
        biophysical_file = os.path.join(S2_SAVEPATH, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
        param_file = os.path.join(S2_SAVEPATH, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
        output = os.path.join(S2_SAVEPATH, "{}_{}_AERO-ROUGH.dim".format(s2.tile_id, s2.str_datetime))
        aerodynamic_roughness(biophysical_file, param_file, output)

        # 8.S3 Pre-Processing (GRAPH)
        gpt = f"/home/eouser/{USER}/esa-snap/bin/gpt"
        S3_L2 = os.path.join(s3.path, s3.name, s3.md_file)
        aoi = WKT_GEOM
        out_obs_geom = os.path.join(S3_SAVEPATH, "LST_OBS-GEOM.dim")
        out_mask = os.path.join(S3_SAVEPATH, "LST_MASK.dim")
        out_lst = os.path.join(S3_SAVEPATH, "LST_data.dim")
        s3_preprocessing(gpt, S3_L2, aoi, out_obs_geom, out_mask, out_lst)
        
        # 9.Warp to template
        source_image = os.path.join(S3_SAVEPATH, "LST_OBS-GEOM.dim")
        temp_image = os.path.join(S2_SAVEPATH, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))
        output_image = os.path.join(S3_SAVEPATH, "LST_OBS-GEOM-REPROJ.dim")
        warp(source_image, temp_image, output_image)

        # 10.Sharpen LST
        s2_refl = os.path.join(S2_SAVEPATH, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))
        s3_lst = os.path.join(S3_SAVEPATH, "LST_data.dim")
        dem = os.path.join(S2_SAVEPATH, "{}_{}_ELEV.dim".format(s2.tile_id, s2.str_datetime))
        geom = os.path.join(S3_SAVEPATH, "LST_OBS-GEOM-REPROJ.dim")
        lst_mask = os.path.join(S3_SAVEPATH, "LST_MASK.dim")
        datetime_utc_str = s3.datetime.strftime("%Y-%m-%d %H:%M")
        datetime_utc = datetime.strptime(datetime_utc_str, "%Y-%m-%d %H:%M")
        output = os.path.join(S3_SAVEPATH, "LST_SHARP.dim")
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
        down_path = os.path.join(METEO_DATAPATH, "meteo_{}_{}.nc".format(start_date, end_date))
        get(CDS_AOI, start_date, end_date, down_path)
        # 12.Prepare ERA5 reanalysis data
        centroid = AOI.geometry[0].centroid
        coordinates = {"lat": centroid.y, "lng": centroid.x, "date_time": s2.datetime}
        offset = get_offset(**coordinates)
        elevation_map = os.path.join(S2_SAVEPATH, "{}_{}_ELEV.dim".format(s2.tile_id, s2.str_datetime))
        ecmwf_data = os.path.join(METEO_DATAPATH, "meteo_{}_{}.nc".format(start_date, end_date))
        date_time_utc = s2.datetime
        time_zone = offset
        output = os.path.join(METEO_DATAPATH, "meteo_{}_{}_PROC".format(start_date, end_date))
        prepare(elevation_map, ecmwf_data, date_time_utc, time_zone, output)

        # 13.Calculate Longwave irradiance
        start_date = str(s2.date - timedelta(days = 1))
        end_date = str(s2.date + timedelta(days = 1))
        meteo = os.path.join(METEO_DATAPATH, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
        output = os.path.join(METEO_DATAPATH, "meteo_{}_LONG_IRRAD.dim".format(s2.date))
        longwave_irradiance(meteo, output)

        # 14. Calculate Net irradiance
        start_date = str(s2.date - timedelta(days = 1))
        end_date = str(s2.date + timedelta(days = 1))
        lsp_product = os.path.join(S2_SAVEPATH, "{}_{}_LEAF-REFL-TRAN.dim".format(s2.tile_id, s2.str_datetime))
        lai_product = os.path.join(S2_SAVEPATH, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
        csp_product = os.path.join(S2_SAVEPATH, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
        mi_product = os.path.join(METEO_DATAPATH, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
        sza_product =  os.path.join(S3_SAVEPATH, "LST_OBS-GEOM-REPROJ.dim")
        output_file = os.path.join(S2_SAVEPATH, "{}_{}_NET-RAD.dim".format(s2.tile_id, s2.str_datetime))
        net_shortwave_radiation(lsp_product, lai_product, csp_product, mi_product, sza_product, output_file)

        # 15. Estimate land surface energy fluxes
        start_date = str(s2.date - timedelta(days = 1))
        end_date = str(s2.date + timedelta(days = 1))
        lst = os.path.join(S3_SAVEPATH, "LST_SHARP.dim")
        lst_vza = os.path.join(S3_SAVEPATH, "LST_OBS-GEOM-REPROJ.dim")
        lai = os.path.join(S2_SAVEPATH, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
        csp =  os.path.join(S2_SAVEPATH, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
        fgv = os.path.join(S2_SAVEPATH, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
        ar = os.path.join(S2_SAVEPATH, "{}_{}_AERO-ROUGH.dim".format(s2.tile_id, s2.str_datetime))
        mi = os.path.join(METEO_DATAPATH, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
        nsr = os.path.join(S2_SAVEPATH, "{}_{}_NET-RAD.dim".format(s2.tile_id, s2.str_datetime))
        li = os.path.join(METEO_DATAPATH, "meteo_{}_LONG_IRRAD.dim".format(s2.date))
        mask = os.path.join(S2_SAVEPATH, "{}_{}_MASK.dim".format(s2.tile_id, s2.str_datetime))
        output_file = os.path.join(S2_SAVEPATH, "{}_{}_EN-FLUX.dim".format(s2.tile_id, s2.str_datetime))
        energy_fluxes(lst, lst_vza, lai, csp, fgv, ar, mi, nsr, li, mask, output_file)

        # 16. Estimate daily evapotranspiration
        start_date = str(s2.date - timedelta(days = 1))
        end_date = str(s2.date + timedelta(days = 1))
        ief_file = os.path.join(S2_SAVEPATH, "{}_{}_EN-FLUX.dim".format(s2.tile_id, s2.str_datetime))
        mi_file = os.path.join(METEO_DATAPATH, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
        output_file = os.path.join(S2_SAVEPATH, "{}_{}_EVAP.dim".format(s2.tile_id, s2.str_datetime))
        daily_evapotranspiration(ief_file, mi_file, output_file)

        print("Done!")

        print("Removing files...")
        # Removing data to free disk space
        for file in os.listdir(S2_SAVEPATH):
            if not (file.endswith("EVAP.dim") or file.endswith("EVAP.data")):
                if file.endswith(".data"):
                    shutil.rmtree(os.path.join(S2_SAVEPATH, file))
                else:
                    os.remove(os.path.join(S2_SAVEPATH, file))
        for file in os.listdir(S3_SAVEPATH):
            if file.endswith(".data"):
                shutil.rmtree(os.path.join(S3_SAVEPATH, file))
            else:
                os.remove(os.path.join(S3_SAVEPATH, file))
        for file in os.listdir(METEO_DATAPATH):
            if file.endswith(".data"):
                shutil.rmtree(os.path.join(METEO_DATAPATH, file))
            else:
                os.remove(os.path.join(METEO_DATAPATH, file))
        
        # Empty cache directory
        cache = "/home/eouser/uth/.snap/var/cache/*"
        os.system(f"rm -rf {cache}")
        gc.collect()