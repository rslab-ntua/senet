from core.ecmwf_utils import download_CDS_data

def get(area:str, start_date:str, end_date:str, download_path:str, download_pressure:bool = True, download_temperature:bool= True,
    download_dewpoint:bool= True, download_wind_speed:bool = True, download_clear_sky_solar_radiation:bool = True, download_solar_radiation:bool= True,
    overwrite:bool = True):
    """Download ECMWF ERA5 reanalysis data from the Climate Data Store (CDS).
    Note that this requires CDS registration and the CDS key located in the right directory
    (see https://cds.climate.copernicus.eu/api-how-to).

    Args:
        area (str): Bounding box coordinates in WGS 84 (format N/W/S/E)
        start_date (str): Start date (format YYYY-MM-DD)
        end_date (str): End date (format YYYY-MM-DD)
        download_path (str): Path to download data in NetCDF format
        download_pressure (bool, optional): Download pressure data. Defaults to True
        download_temperature (bool, optional): Download temperature data. Defaults to True
        download_dewpoint (bool, optional): Download dewpoint temperature data. Defaults to True
        download_wind_speed (bool, optional): Download wind speed data. Defaults to True
        download_clear_sky_solar_radiation (bool, optional): Download clear sky radiation data. Defaults to True
        download_solar_radiation (bool, optional): Download solar radiation data. Defaults to True
        overwrite (bool, optional): Overwrite file if exists. Defaults to True
    """
    fields = []
    if download_temperature:
        fields.extend(['2m_temperature', 'z', '2m_dewpoint_temperature', 'surface_pressure'])
    if download_dewpoint and '2m_dewpoint_temperature' not in fields:
        fields.append('2m_dewpoint_temperature')
    if download_pressure and 'surface_pressure' not in fields:
        fields.append('surface_pressure')
    if download_wind_speed:
        fields.extend(['100m_v_component_of_wind', '100m_u_component_of_wind'])
    if download_clear_sky_solar_radiation:
        fields.append("surface_solar_radiation_downward_clear_sky")
    if download_solar_radiation:
        fields.append('surface_solar_radiation_downwards')
    
    download_CDS_data(start_date, end_date, fields, download_path, overwrite, area)
