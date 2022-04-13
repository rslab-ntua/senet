import numpy as np
from pyTSEB import meteo_utils as met

import core.snappy_utils as su

def daily_evapotranspiration(ief_file:str, mi_file:str, output_file:str):
    """Estimates daily evapotranspiration by extrapolating instantaneous latent heat flux using daily solar irradiance.

    Args:
        ief_file (str): Path to energy fluxes product
        mi_file (str): Path to meteorological data product (from prepare)
        output_file (str): Path to store daily evapotranspiration [mm/day]
    """

    # Read the required data
    le_band, geo_coding = su.read_snappy_product(ief_file, 'latent_heat_flux')
    le_band = le_band.astype(np.float32)
    sdn_band = su.read_snappy_product(mi_file, 'clear_sky_solar_radiation')[0].astype(np.float32)
    sdn_24_band = su.read_snappy_product(mi_file, 'average_daily_solar_irradiance')[0].astype(np.float32)

    le = np.array(le_band)
    sdn = np.array(sdn_band)
    sdn_24 = np.array(sdn_24_band)

    et_daily = met.flux_2_evaporation(sdn_24 * le / sdn, t_k=20+273.15, time_domain=24)
    
    su.write_snappy_product(output_file, [{'band_name': 'daily_evapotranspiration', 'band_data': et_daily}],
                            'dailySpectra', geo_coding)
