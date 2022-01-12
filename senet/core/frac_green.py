import numpy as np
from pyTSEB import TSEB
import core.snappy_utils as su

def fraction_green(sza_file:str, biophysical_file:str, min_frac_green:float, output_file:str):
    """Estimates the fraction of vegetation which is green based on the leaf area index (LAI),
    fraction of absorb ed photosynthetically active radiation (FAPAR) and sun zenith angle bands.
    Bare ground takes 0 value while green live vegetation 1.

    Args:
        sza_file (str, pathlike): Path to Sentinel-2 sun zenith angle product
        biophysical_file (str, pathlike): Path to Sentinel-2 biophysical product
        min_frac_green (float): Minimum fraction of vegetation which is green. Range from 0.01 to 1
        output_file (str): Product containing the fraction of green vegetation data
    """
    if (min_frac_green > 1) or (min_frac_green<0.01):
        raise ValueError("min_frac_green must be between 0.01 and 1!")
    # Read the required data
    fapar, geo_coding = su.read_snappy_product(biophysical_file, 'fapar')
    fapar = fapar.astype(np.float32)
    lai = su.read_snappy_product(biophysical_file, 'lai')[0].astype(np.float32)
    sza = su.read_snappy_product(sza_file, 'sun_zenith')[0].astype(np.float32)

    # Calculate fraction of vegetation which is green
    f_g = np.ones(lai.shape, np.float32)
    # Iterate until f_g converges
    converged = np.zeros(lai.shape, dtype=bool)
    # For pixels where LAI or FAPAR are below tolerance threshold of the S2 biophysical
    # processor, assume that the soil is bare and f_g = 1
    converged[np.logical_or(lai <= 0.2, fapar <= 0.1)] = True
    for c in range(50):
        f_g_old = f_g.copy()
        fipar = TSEB.calc_F_theta_campbell(sza[~converged],
                                           lai[~converged]/f_g[~converged],
                                           w_C=1, Omega0=1, x_LAD=1)
        f_g[~converged] = fapar[~converged] / fipar
        f_g = np.clip(f_g, min_frac_green, 1.)
        converged = np.logical_or(np.isnan(f_g), np.abs(f_g - f_g_old) < 0.02)
        if np.all(converged):
            break

    su.write_snappy_product(output_file, [{'band_name': 'frac_green', 'band_data': f_g}],
                            'fracGreen', geo_coding)
