import numpy as np
import core.snappy_utils as su

def cab_to_vis_spectrum(cab:np.array, coeffs_wc_rho_vis:list=[0.14096573, -0.09648072, -0.06328343], coeffs_wc_tau_vis:list=[0.08543707, -0.08072709, -0.06562554]):
    """Estimates leaf reflectance and transmittance on visible spectrum.

    Args:
        cab (np.array): Chlorophyll content in the leaf product from S2 pre-processing [μg/cm^{2}]
        coeffs_wc_rho_vis (list, optional): Visible spectrum reflectance water cloud model coefficients. Defaults to [0.14096573, -0.09648072, -0.06328343]
        coeffs_wc_tau_vis (list, optional): Visible spectrum transmittance water cloud model coefficients. Defaults to [0.08543707, -0.08072709, -0.06562554]

    Returns:
        tuple: Leaf reflectance [np.array] and transmittance [np.array] on visible spectrum
    """
    rho_leaf_vis = watercloud_model(cab, *coeffs_wc_rho_vis)
    tau_leaf_vis = watercloud_model(cab, *coeffs_wc_tau_vis)

    rho_leaf_vis = np.clip(rho_leaf_vis, 0, 1)
    tau_leaf_vis = np.clip(tau_leaf_vis, 0, 1)

    return rho_leaf_vis, tau_leaf_vis

def cw_to_nir_spectrum(cw:np.array, coeffs_wc_rho_nir:list=[0.38976106, -0.17260689, -65.7445699], coeffs_wc_tau_nir:list=[0.36187620, -0.18374560, -65.3125878]):
    """Estimates leaf reflectance and transmittance on NIR spectrum.

    Args:
        cab (np.array): Chlorophyll content in the leaf product from S2 pre-processing [ug/cm^{2}]
        coeffs_wc_rho_vis (list, optional): NIR spectrum reflectance water cloud model coefficients. Defaults to [0.14096573, -0.09648072, -0.06328343]
        coeffs_wc_tau_vis (list, optional): NIR spectrum transmittance water cloud model coefficients. Defaults to [0.08543707, -0.08072709, -0.06562554]

    Returns:
        tuple: Leaf reflectance [np.array] and transmittance [np.array] on NIR spectrum
    """
    rho_leaf_nir = watercloud_model(cw, *coeffs_wc_rho_nir)
    tau_leaf_nir = watercloud_model(cw, *coeffs_wc_tau_nir)

    rho_leaf_nir = np.clip(rho_leaf_nir, 0, 1)
    tau_leaf_nir = np.clip(rho_leaf_nir, 0, 1)

    return rho_leaf_nir, tau_leaf_nir

def watercloud_model(param:np.array, a:float, b:float, c:float):
    """Applies WCM."""

    result = a + b * (1.0 - np.exp(c * param))

    return result

def leaf_spectra(biophysical_file:str, output_file:str):
    """Estimates leaf reflectance and transmittance based on plant chlorophyl and water content.
    
    Args:
        biophysical_file (str, path-like): Path to biophysical file exported from sentinel 2 pre-processing 
        output_file (str, path-like): Path to store the output leaf spectral properties in BEAM-DIMAP product
    """
    # Read the required data
    lai_cab, geo_coding = su.read_snappy_product(biophysical_file, 'lai_cab')
    lai_cw = su.read_snappy_product(biophysical_file, 'lai_cw')[0]
    
    cab = np.clip(np.array(lai_cab), 0.0, 140.0)
    refl_vis, trans_vis = cab_to_vis_spectrum(cab)

    cw = np.clip(np.array(lai_cw), 0.0, 0.1)
    refl_nir, trans_nir = cw_to_nir_spectrum(cw)

    su.write_snappy_product(output_file, [
        {'band_name': 'refl_vis_c', 'band_data': refl_vis},
        {'band_name': 'refl_nir_c', 'band_data': refl_nir},
        {'band_name': 'trans_vis_c', 'band_data': trans_vis},
        {'band_name': 'trans_nir_c', 'band_data': trans_nir}
        ],
        'leafSpectra', geo_coding)
