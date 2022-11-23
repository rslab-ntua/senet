import numpy as np

import pyTSEB.net_radiation as rad
import senet.core.snappy_utils as su

def longwave_irradiance(meteo_product:str, output_file:str, at_band:str = "air_temperature", vp_band:str = "vapour_pressure", ap_band:str = "air_pressure", at_height:float = 100.0):
    """Estimates atmosphere longwave irradiance [W/m^{2}] based on meteorological inputs.

    Args:
        meteo_product (str): Meteorological inputs product of prepare ERA5 reanalysis data
        output_file (str): Product to store longwave irradiance data
        at_band (str, optional): Band name that contains air temperature data. Defaults to "air_temperature".
        vp_band (str, optional): Band name that contains vapour pressure data. Defaults to "vapour_pressure".
        ap_band (str, optional): Band name that contains air pressure data. Defaults to "air_pressure".
        at_height (float, optional): Reference height of data. Defaults to 100.0.
    """

    at, geo_coding = su.read_snappy_product(meteo_product, at_band)
    at = at.astype(np.float32)
    vp = su.read_snappy_product(meteo_product, vp_band)[0].astype(np.float32)
    ap = su.read_snappy_product(meteo_product, ap_band)[0].astype(np.float32)

    irrad = rad.calc_longwave_irradiance(vp, at, ap, at_height)
    
    band_data = [
            {'band_name': 'longwave_irradiance', 'band_data': irrad}
    ]

    su.write_snappy_product(output_file, band_data, 'longwaveIrradiance', geo_coding)
