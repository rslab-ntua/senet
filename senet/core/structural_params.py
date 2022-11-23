import numpy as np
import senet.core.snappy_utils as su
import os
path =  os.path.dirname(os.path.abspath(__file__))
auxdata = os.path.join(path, "../auxdata")

def _estimate_param_value(landcover:np.array, lut:dict, band:str): 
    """Get LUT value for a category.

    Args:
        landcover (np.array): Array with landcover values
        lut (dict): Dictionary with landcover values as keys and auxiliary values
        band (str): lut dictionary key value 

    Returns:
        float: Value for a specific band
    """
    param_value = np.ones(landcover.shape) + np.nan

    for lc_class in np.unique(landcover[~np.isnan(landcover)]):
        lc_pixels = np.where(landcover == lc_class)
        lc_index = lut['landcover_class'].index(lc_class)
        param_value[lc_pixels] = lut[band][lc_index]
    return param_value

def str_parameters(landcover_map:str, lai_map:str, fgv_map:str, landcover_band:str, produce_vh:bool, produce_fc:bool,
    produce_chwr:bool, produce_lw:bool, produce_lid:bool, produce_igbp:bool, output_file:str, lookup_table:str = os.path.join(auxdata, "LUT/ESA_CCI_LUT.csv")):
    """Produces maps of vegetation structural parameters required for TSEB model, based on a land cover map and a look-up table (LUT).

    Args:
        landcover_map (str): Path to landcover product
        lai_map (str): Path to biophysical product
        fgv_map (str): Path to fraction of green vegetation product
        landcover_band (str): Name of landcover band as produced
        produce_vh (bool): Indicate if the vegetation height maps should be produced
        produce_fc (bool): Indicate if the vegetation fractional cover maps should be produced
        produce_chwr (bool): Indicate if the canopy to width ratio maps should be produced
        produce_lw (bool): Indicate if the leaf width maps should be produced
        produce_lid (bool): Indicate if the leaf inclination distribution maps should be produced
        produce_igbp (bool): Indicate if the landcover map with IGBP classes should be produced
        output_file (str): Path to store product containing the maps of vegetation structural parameters
        lookup_table (str, optional): Path to LUT table data. Defaults to "../auxdata/LUT/ESA_CCI_LUT.csv"
    """

    # Read the required data
    PARAMS = ['veg_height', 'lai_max', 'is_herbaceous', 'veg_fractional_cover',
              'veg_height_width_ratio', 'veg_leaf_width', 'veg_inclination_distribution',
              'igbp_classification'
              ]
    
    landcover, geo_coding = su.read_snappy_product(landcover_map, landcover_band)
    landcover = landcover.astype(np.float32)
    lai = su.read_snappy_product(lai_map, 'lai')[0].astype(np.float32)
    fg = su.read_snappy_product(fgv_map, 'frac_green')[0].astype(np.float32)
    with open(lookup_table, 'r') as fp:
        lines = fp.readlines()
    headers = lines[0].rstrip().split(';')
    values = [x.rstrip().split(';') for x in lines[1:]]
    lut = {key: [float(x[idx]) for x in values if len(x) == len(headers)]
            for idx, key in enumerate(headers)}
    for param in PARAMS:
        if param not in lut.keys():
            print(f'Error: Missing {param} in the look-up table')
            return

    band_data = []
    param_value = np.ones(landcover.shape, np.float32) + np.nan

    if produce_vh:
        for lc_class in np.unique(landcover[~np.isnan(landcover)]):
            lc_pixels = np.where(landcover == lc_class)
            lc_index = lut["landcover_class"].index(lc_class)
            param_value[lc_pixels] = lut['veg_height'][lc_index]

            # Vegetation height in herbaceous vegetation depends on plant area index
            if lut["is_herbaceous"][lc_index] == 1:
                pai = lai / fg
                pai = pai[lc_pixels]
                param_value[lc_pixels] = \
                    0.1 * param_value[lc_pixels] + 0.9 * param_value[lc_pixels] *\
                    np.minimum((pai / lut['veg_height'][lc_index])**3.0, 1.0)
        band_data.append({'band_name': 'veg_height', 'band_data': param_value})
    
    if produce_fc:
        band_name = 'veg_fractional_cover'
        param_value = _estimate_param_value(landcover, lut, band_name)
        band_data.append({'band_name': band_name, 'band_data': param_value})
    
    if produce_chwr:
        band_name = 'veg_height_width_ratio'
        param_value = _estimate_param_value(landcover, lut, band_name)
        band_data.append({'band_name': band_name, 'band_data': param_value})

    if produce_lw:
        band_name = 'veg_leaf_width'
        param_value = _estimate_param_value(landcover, lut, band_name)
        band_data.append({'band_name': band_name, 'band_data': param_value})

    if produce_lid:
        band_name = 'veg_inclination_distribution'
        param_value = _estimate_param_value(landcover, lut, band_name)
        band_data.append({'band_name': band_name, 'band_data': param_value})

    if produce_igbp:
        band_name = 'igbp_classification'
        param_value = _estimate_param_value(landcover, lut, band_name)
        band_data.append({'band_name': band_name, 'band_data': param_value})

    su.write_snappy_product(output_file, band_data, 'landcoverParams', geo_coding)