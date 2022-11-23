import tempfile
import senet.core.ecmwf_utils as eu
# snappy_utils should be imported last, as it modifies the system path
import senet.core.snappy_utils as su
import datetime

def prepare(elevation_map:str, ecmwf_data_file:str, date_time_utc:datetime.datetime, time_zone:float, output_file:str, elevation_band:str = "elevation",
    prepare_temperature:bool = True, prepare_vapour_pressure:bool = True, prepare_air_pressure:bool = True,
    prepare_wind_speed:bool = True, prepare_clear_sky_solar_radiation:bool = True, prepare_daily_solar_irradiance:bool = True):
    """Prepares ERA5 reanalysis surface meteorological data based on the ECMWF ERA5 reanalysis data and the high resolution DEM.

    Args:
        elevation_map (str): Path to high resolution DEM (output of elevation graph)
        ecmwf_data_file (str): Path to ECMWF NetCDF file
        date_time_utc (datetime.datetime): Date and time (UTC) for which to prepare meteorological data (YYYY-MM-DD HH:MM)
        output_file (str): Path to save file
        time_zone (float): Time zone of the center of area of interest
        elevation_band (str, optional): Name of elevation band. Defaults to "elevation"
        prepare_temperature (bool, optional): Prepare temperature. Defaults to True
        prepare_vapour_pressure (bool, optional): Prepare vapour pressure. Defaults to True
        prepare_air_pressure (bool, optional): Prepare air pressure. Defaults to True
        prepare_wind_speed (bool, optional): Prepare wind speed. Defaults to True
        prepare_clear_sky_solar_radiation (bool, optional): Prepare clear sky solar radiation. Defaults to True
        prepare_daily_solar_irradiance (bool, optional): Prepare daily solar irradiance. Defaults to True
    """
    # Save elevation to GeoTIFF because it will need to be read by GDAL later
    temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    temp_elev_path = temp_file.name
    temp_file.close()
    su.copy_bands_to_file(elevation_map, temp_elev_path, [elevation_band])

    # Calculate required meteorological parameters
    bands = []
    if prepare_temperature:
        data = eu.get_ECMWF_data(ecmwf_data_file, 'air_temperature', date_time_utc, temp_elev_path,
                                 time_zone)
        bands.append({'band_data': data, 'band_name': 'air_temperature', 'description':
                      'Air temperature at 100 m above surface(K)'})
    if prepare_vapour_pressure:
        data = eu.get_ECMWF_data(ecmwf_data_file, 'vapour_pressure', date_time_utc, temp_elev_path,
                                 time_zone)
        bands.append({'band_data': data, 'band_name': 'vapour_pressure', 'description':
                      'Surface vapour pressure (mb)'})
    if prepare_air_pressure:
        data = eu.get_ECMWF_data(ecmwf_data_file, 'air_pressure', date_time_utc, temp_elev_path,
                                 time_zone)
        bands.append({'band_data': data, 'band_name': 'air_pressure', 'description':
                      'Surface air pressure (mb)'})
    if prepare_wind_speed:
        data = eu.get_ECMWF_data(ecmwf_data_file, 'wind_speed', date_time_utc, temp_elev_path,
                                 time_zone)
        bands.append({'band_data': data, 'band_name': 'wind_speed', 'description':
                      'Wind speed at 100 m above surface (m/s)'})
    if prepare_clear_sky_solar_radiation:
        data = eu.get_ECMWF_data(ecmwf_data_file, 'clear_sky_solar_radiation', date_time_utc,
                                 temp_elev_path, time_zone)
        bands.append({'band_data': data, 'band_name': 'clear_sky_solar_radiation', 'description':
                      'Instantenous clear sky surface solar irradiance (W/m^2)'})
    if prepare_daily_solar_irradiance:
        data = eu.get_ECMWF_data(ecmwf_data_file, 'average_daily_solar_irradiance', date_time_utc,
                                 temp_elev_path, time_zone)
        bands.append({'band_data': data, 'band_name': 'average_daily_solar_irradiance',
                      'description': 'Average daily solar irradiance (W/m^2)'})

    # Save the output file
    geo_coding = su.read_snappy_product(elevation_map, elevation_band)[1]
    su.write_snappy_product(output_file, bands, 'ecmwfData', geo_coding)
