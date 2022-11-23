import tempfile
import numpy as np
import os
import os.path as pth

from pyDMS.pyDMS import DecisionTreeSharpener

import senet.core.gdal_utils as gu
import senet.core.snappy_utils as su

def sharpen(sentinel_2_reflectance:str, sentinel_3_lst:str, high_res_dem:str, high_res_geom:str, lst_quality_mask:str,
    date_time_utc:str, output:str, elevation_band:str = "elevation", cv_homogeneity_threshold:float = .0, lst_good_quality_flags:str = "1",
    moving_window_size:int = 30, parallel_jobs:int = 1):
    """Data Mining Sharpener Python implementation for sharpening SLSTR Land Surface Temperature to Sentinel-2 spatial resolution.

    Args:
        sentinel_2_reflectance (str, pathlike): Path to Sentinel 2 reflectance product (from S2-Preprocessing)
        sentinel_3_lst (str, pathlike): Path to LST S3 SLSTR L2 product (from S3-Preprocessing)
        high_res_dem (str, pathlike): Path to high resolution DEM product (from S2-Preprocessing)
        high_res_geom (str, pathlike): Path to high resolution S3 geometry observation product (from wrap)
        lst_quality_mask (str, pathlike): Path to quality mask product (from S3-Preprocessing)
        date_time_utc (str): S3 acquisition date and time (UTC) in YYYY-MM-DD HH:MM string format
        output (str, pathlike): Path to output result
        elevation_band (str, optional): Name of elevation band. Defaults to "elevation"
        cv_homogeneity_threshold (float, optional): Homogeneity inclusion threshold from [0, 1]. Defaults to .0 
        lst_good_quality_flags (str, optional):Good quality mask values. Defaults to "1"      
        moving_window_size (int, optional): Moving window size. Defaults to 3
        parallel_jobs (int, optional): Parallel jobs. Defaults to 1
    """

    # Derive illumination conditions from the DEM
    print('INFO: Deriving solar illumination conditions...')
    temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    temp_dem_file = temp_file.name
    temp_file.close()
    su.copy_bands_to_file(high_res_dem, temp_dem_file, [elevation_band])
    temp_slope_file = gu.slope_from_dem(temp_dem_file)
    temp_aspect_file = gu.aspect_from_dem(temp_dem_file)
    slope = gu.raster_data(temp_slope_file)
    aspect = gu.raster_data(temp_aspect_file)
    try:
        lat = su.read_snappy_product(high_res_geom, 'latitude_tx')[0]
    except RuntimeError:
        lat = su.read_snappy_product(high_res_geom, 'latitude_in')[0]
    try:
        lon = su.read_snappy_product(high_res_geom, 'longitude_tx')[0]
    except RuntimeError:
        lon = su.read_snappy_product(high_res_geom, 'longitude_in')[0]
    doy = date_time_utc.timetuple().tm_yday
    ftime = date_time_utc.hour + date_time_utc.minute/60.0
    cos_theta = incidence_angle_tilted(lat, lon, doy, ftime, stdlon=0, A_ZS=aspect, slope=slope)
    proj, gt = gu.raster_info(temp_dem_file)[0:2]
    temp_cos_theta_file = pth.splitext(temp_dem_file)[0] + '_cos_theta.tif'
    fp = gu.save_image(cos_theta, gt, proj, temp_cos_theta_file)
    fp = None
    slope = None
    aspect = None
    cos_theta = None

    print('INFO: Preparing high-resolution data...')
    # Combine all high-resolution data into one virtual raster
    temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    temp_refl_file = temp_file.name
    temp_file.close()
    su.copy_bands_to_file(sentinel_2_reflectance, temp_refl_file)
    vrt_filename = pth.splitext(temp_refl_file)[0]+".vrt"
    fp = gu.merge_raster_layers([temp_refl_file, temp_dem_file, temp_cos_theta_file],
                                vrt_filename, separate=True)
    fp = None
    high_res_filename = vrt_filename

    # Save low resolution files as geotiffs
    temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    temp_lst_file = temp_file.name
    temp_file.close()
    su.copy_bands_to_file(sentinel_3_lst, temp_lst_file, ["LST"])
    temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    temp_mask_file = temp_file.name
    temp_file.close()
    su.copy_bands_to_file(lst_quality_mask, temp_mask_file)

    # Set options of the disaggregator
    flags = [int(i) for i in lst_good_quality_flags.split(",")]
    dms_options =\
        {"highResFiles": [high_res_filename],
         "lowResFiles": [temp_lst_file],
         "lowResQualityFiles": [temp_mask_file],
         "lowResGoodQualityFlags": flags,
         "cvHomogeneityThreshold": cv_homogeneity_threshold,
         "movingWindowSize": moving_window_size,
         "disaggregatingTemperature":  True,
         "baggingRegressorOpt":        {"n_jobs": parallel_jobs, "n_estimators": 30,
                                        "max_samples": 0.8, "max_features": 0.8}}
    disaggregator = DecisionTreeSharpener(**dms_options)

    # Do the sharpening
    print("INFO: Training regressor...")
    disaggregator.trainSharpener()
    print("INFO: Sharpening...")
    downscaled_file = disaggregator.applySharpener(high_res_filename, temp_lst_file)
    print("INFO: Residual analysis...")
    residual_image, corrected_image = disaggregator.residualAnalysis(downscaled_file,
                                                                     temp_lst_file,
                                                                     temp_mask_file,
                                                                     doCorrection=True)
    # Save the sharpened file
    band = {"band_name": "sharpened_LST", "description": "Sharpened Sentinel-3 LST", "unit": "K",
            "band_data": corrected_image.GetRasterBand(1).ReadAsArray()}
    geo_coding = su.get_product_info(sentinel_2_reflectance)[1]
    su.write_snappy_product(output, [band], "sharpenedLST", geo_coding)

    # Clean up
    try:
        os.remove(temp_dem_file)
        os.remove(temp_aspect_file)
        os.remove(temp_slope_file)
        os.remove(temp_cos_theta_file)
        os.remove(temp_refl_file)
        os.remove(temp_lst_file)
        os.remove(temp_mask_file)
    except Exception:
        pass


def declination_angle(doy:int):
    """Calculates the Earth declination angle.

    Args:
        doy (int, float): Day of year

    Returns:
        float: Declination angle [radians]
    """

    declination = np.radians(23.45) * np.sin((2.0 * np.pi * doy / 365.0) - 1.39)

    return declination


def hour_angle(ftime:float, declination:float, lon:float, stdlon:float = .0):
    """Calculates the hour angle.

    Args:
        ftime (float): Time of the day [decimal hours]
        declination (float): Declination angle [radians]
        lon (float): Longitude of the site [degrees]
        stdlon (float, optional): Longitude of the standard meridian that represents ftime time zone. Defaults to 0.

    Returns:
        float: hour angle [radians]
    """

    EOT = 0.258 * np.cos(declination) - 7.416 * np.sin(declination) - \
          3.648 * np.cos(2.0 * declination) - 9.228 * np.sin(2.0 * declination)
    LC = (stdlon - lon) / 15.
    time_corr = (-EOT / 60.) + LC
    solar_time = ftime - time_corr
    # Get the hour angle
    w = np.radians((12.0 - solar_time) * 15.)

    return w


def incidence_angle_tilted(lat:float, lon:float, doy:int, ftime:float, stdlon:float = .0, A_ZS:float = .0, slope:float = .0):
    """Calculates the incidence solar angle over a tilted flat surface.

    Args:
        lat (float, np.array): Latitude [degrees]
        lon (float, np.array): Longitude [degrees]
        doy (int): Day of year
        ftime (float): Time of the day [decimal hours]
        stdlon (float, optional): Longitude of the standard meridian that represents ftime time zone. Defaults to .0
        A_ZS (float, np.array, optional): Surface azimuth angle, measured clockwise from north [degrees]. Defaults to .0
        slope (float, optional): Slope angle [radians]. Defaults to .0

    Returns:
        [float, np.array]: Cosine of the incidence angle
    """

    # Get the declination and hour angle
    delta = declination_angle(doy)
    omega = hour_angle(ftime, delta, lon, stdlon=stdlon)

    # Convert remaining angles into radians
    lat, A_ZS, slope = map(np.radians, [lat, A_ZS, slope])

    cos_theta_i = (np.sin(delta) * np.sin(lat) * np.cos(slope)
                   + np.sin(delta) * np.cos(lat) * np.sin(slope) * np.cos(A_ZS)
                   + np.cos(delta) * np.cos(lat) * np.cos(slope) * np.cos(omega)
                   - np.cos(delta) * np.sin(lat) * np.sin(slope) * np.cos(A_ZS) * np.cos(omega)
                   - np.cos(delta) * np.sin(slope) * np.sin(A_ZS) * np.sin(omega))

    return cos_theta_i