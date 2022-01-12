import numpy as np
from pyTSEB import TSEB

import core.snappy_utils as su

def energy_fluxes(lst:str, lst_vza:str, lai:str, csp:str, fgv:str, ar:str, mi:str, nsr:str, li:str, mask:str, output_file:str, soil_roughness:float = .01, alpha_pt:float = 1.28,
    atmospheric_measurement_height:float = 100.0, green_vegetation_emissivity:float = 0.99, soil_emissivity:float = 0.99, save_component_fluxes:bool = True,
    save_component_temperature:bool = True, save_aerodynamic_parameters:bool = True):
    """Estimates land surface energy fluxes (latent, sensible, ground heat and net radiation) using One-Source Energy Balance model for bare soil pixels and Two-Source Energy Balance
    model for vegetated pixels.

    Args:
        lst (str): Sharpened land surface temperature product (from sharpen)
        lst_vza (str): LST view zenith angle product (from S3 wrap)
        lai (str): Plant biophysical properties product
        csp (str): Vegetation structural parameters product
        fgv (str): Fraction of green vegetation product
        ar (str): Aerodynamic roughness product
        mi (str): Meteorological inputs product (from prepare)
        nsr (str): Net shortwave radiation product
        li (str): Longwave irradiance product
        mask (str): Sentinel-2 mask product
        output_file (str): Path to store land surface energy fluxes product
        soil_roughness (float, optional): Soil roughness [m]. Defaults to .01.
        alpha_pt (float, optional): Alpha pt. Defaults to 1.28.
        atmospheric_measurement_height (float, optional): Atmospheric measurement height [m]. Defaults to 100.0.
        green_vegetation_emissivity (float, optional): Green vegetation emissivity. Defaults to 0.99.
        soil_emissivity (float, optional): Soil emissivity. Defaults to 0.99.
        save_component_fluxes (bool, optional): Save component fluxes data. Defaults to True.
        save_component_temperature (bool, optional): Save component temperature data. Defaults to True.
        save_aerodynamic_parameters (bool, optional): Save aerodynamic parameters. Defaults to True.
    """
    # Read the required data
    lst = su.read_snappy_product(lst, 'sharpened_LST')[0].astype(np.float32)
    vza = su.read_snappy_product(lst_vza, 'sat_zenith_tn')[0].astype(np.float32)
    lai, geo_coding = su.read_snappy_product(lai, 'lai')
    lai = lai.astype(np.float32)
    lad = su.read_snappy_product(csp, 'veg_inclination_distribution')[0].astype(np.float32)
    frac_cover = su.read_snappy_product(csp, 'veg_fractional_cover')[0].astype(np.float32)
    h_w_ratio = su.read_snappy_product(csp, 'veg_height_width_ratio')[0].astype(np.float32)
    leaf_width = su.read_snappy_product(csp, 'veg_leaf_width')[0].astype(np.float32)
    veg_height = su.read_snappy_product(csp, 'veg_height')[0].astype(np.float32)
    landcover_band = su.read_snappy_product(csp, 'igbp_classification')[0].astype(np.float32)
    frac_green = su.read_snappy_product(fgv, 'frac_green')[0].astype(np.float32)
    z_0M = su.read_snappy_product(ar, 'roughness_length')[0].astype(np.float32)
    d_0 = su.read_snappy_product(ar, 'zero_plane_displacement')[0].astype(np.float32)
    ta = su.read_snappy_product(mi, 'air_temperature')[0].astype(np.float32)
    u = su.read_snappy_product(mi, 'wind_speed')[0].astype(np.float32)
    ea = su.read_snappy_product(mi, 'vapour_pressure')[0].astype(np.float32)
    p = su.read_snappy_product(mi, 'air_pressure')[0].astype(np.float32)
    shortwave_rad_c = su.read_snappy_product(nsr, 'net_shortwave_radiation_canopy')[0].astype(np.float32)
    shortwave_rad_s = su.read_snappy_product(nsr, 'net_shortwave_radiation_soil')[0].astype(np.float32)
    longwave_irrad = su.read_snappy_product(li, 'longwave_irradiance')[0].astype(np.float32)
    mask = su.read_snappy_product(mask, 'mask')[0].astype(np.float32)

    # Model outputs
    t_s = np.full(lai.shape, np.nan, np.float32)
    t_c = np.full(lai.shape, np.nan, np.float32)
    t_ac = np.full(lai.shape, np.nan, np.float32)
    h_s = np.full(lai.shape, np.nan, np.float32)
    h_c = np.full(lai.shape, np.nan, np.float32)
    le_s = np.full(lai.shape, np.nan, np.float32)
    le_c = np.full(lai.shape, np.nan, np.float32)
    g = np.full(lai.shape, np.nan, np.float32)
    ln_s = np.full(lai.shape, np.nan, np.float32)
    ln_c = np.full(lai.shape, np.nan, np.float32)
    r_s = np.full(lai.shape, np.nan, np.float32)
    r_x = np.full(lai.shape, np.nan, np.float32)
    r_a = np.full(lai.shape, np.nan, np.float32)
    u_friction = np.full(lai.shape, np.nan, np.float32)
    mol = np.full(lai.shape, np.nan, np.float32)
    n_iterations = np.full(lai.shape, np.nan, np.float32)
    flag = np.full(lai.shape, 255)

    # ======================================
    # First process bare soil cases
    i = np.logical_and(lai <= 0, mask == 1)
    t_s[i] = lst[i]

    # Calculate soil fluxes
    [flag[i], ln_s[i], le_s[i], h_s[i], g[i], r_a[i], u_friction[i], mol[i],
    n_iterations[i]] = TSEB.OSEB(lst[i],
                                 ta[i],
                                 u[i],
                                 ea[i],
                                 p[i],
                                 shortwave_rad_s[i],
                                 longwave_irrad[i],
                                 soil_emissivity,
                                 z_0M[i],
                                 d_0[i],
                                 atmospheric_measurement_height,
                                 atmospheric_measurement_height,
                                 calcG_params=[[1], 0.35])

    # Set canopy fluxes to 0
    ln_c[i] = 0.0
    le_c[i] = 0.0
    h_c[i] = 0.0

    # ======================================
    # Then process vegetated cases
    i = np.logical_and(lai > 0, mask == 1)
    # Emissivity of canopy containing green and non-green elements.
    emissivity_veg = green_vegetation_emissivity * frac_green[i] + 0.91 * (1 - frac_green[i])

    # Caculate component fluxes
    [flag[i], t_s[i], t_c[i], t_ac[i], ln_s[i], ln_c[i], le_c[i], h_c[i], le_s[i], h_s[i],
    g[i], r_s[i], r_x[i], r_a[i], u_friction[i], mol[i],
    n_iterations[i]] = TSEB.TSEB_PT(lst[i],
                                    vza[i],
                                    ta[i],
                                    u[i],
                                    ea[i],
                                    p[i],
                                    shortwave_rad_c[i],
                                    shortwave_rad_s[i],
                                    longwave_irrad[i],
                                    lai[i],
                                    veg_height[i],
                                    emissivity_veg,
                                    soil_emissivity,
                                    z_0M[i],
                                    d_0[i],
                                    atmospheric_measurement_height,
                                    atmospheric_measurement_height,
                                    f_c=frac_cover[i],
                                    f_g=frac_green[i],
                                    w_C=h_w_ratio[i],
                                    leaf_width=leaf_width[i],
                                    z0_soil=soil_roughness,
                                    alpha_PT=alpha_pt,
                                    x_LAD=lad[i],
                                    calcG_params=[[1], 0.35],
                                    resistance_form=[0, {}])

    # Calculate the bulk fluxes
    le = le_c + le_s
    h = h_c + h_s
    r_ns = shortwave_rad_c + shortwave_rad_s
    r_nl = ln_c + ln_s
    r_n = r_ns + r_nl

    band_data = [
            {'band_name': 'sensible_heat_flux', 'band_data': h},
            {'band_name': 'latent_heat_flux', 'band_data': le},
            {'band_name': 'ground_heat_flux', 'band_data': g},
            {'band_name': 'net_radiation', 'band_data': r_n},
            {'band_name': 'quality_flag', 'band_data': flag}
            ]

    if save_component_fluxes:
        band_data.extend(
                [
                    {'band_name': 'sensible_heat_flux_canopy', 'band_data': h_c},
                    {'band_name': 'sensible_heat_flux_soil', 'band_data': h_s},
                    {'band_name': 'latent_heat_flux_canopy', 'band_data': le_c},
                    {'band_name': 'latent_heat_flux_soil', 'band_data': le_s},
                    {'band_name': 'net_longwave_radiation_canopy', 'band_data': ln_c},
                    {'band_name': 'net_longwave_radiation_soil', 'band_data': ln_s}
                ]
        )
    if save_component_temperature:
        band_data.extend(
                [
                    {'band_name': 'temperature_canopy', 'band_data': t_c}, 
                    {'band_name': 'temperature_soil', 'band_data': t_s},
                    {'band_name': 'temperature_canopy_air', 'band_data': t_ac}
                ]
        )
    if save_aerodynamic_parameters:
        band_data.extend(
                [ 
                    {'band_name': 'resistance_surface', 'band_data': r_a}, 
                    {'band_name': 'resistance_canopy', 'band_data': r_x},
                    {'band_name': 'resistance_soil', 'band_data': r_s},
                    {'band_name': 'friction_velocity', 'band_data': u_friction},
                    {'band_name': 'monin_obukhov_length', 'band_data': mol}
                ]
        )
    
    su.write_snappy_product(output_file, band_data, 'turbulentFluxes', geo_coding)
