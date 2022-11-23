import subprocess
import os

path =  os.path.dirname(os.path.abspath(__file__))
auxdata = os.path.join(path, "../auxdata")

def s2_preprocessing(gpt_path:str, S2_L2A:str, AOI:str,
    out_refl:str, out_sun_zenith:str, out_mask:str, out_bio:str):
    """Running pre-processing procedures for Sentinel 2 data.

    Args:
        gpt_path (str): Path to SNAP GPT
        S2_L2A (str): Path to Sentinel 2 L2A data
        AOI (str): WKT geometry as string
        out_refl (str): Path to store the output reflectance product
        out_sun_zenith (str): Path to store sun zenith angles product
        out_mask (str): Path to store the output mask product
        out_bio (str): Path to store the output bio product
    """

    subprocess.run([gpt_path, os.path.join(auxdata, "sentinel_2_preprocessing.xml"),
        "-PINPUT_S2_L2A={}".format(S2_L2A),
        "-PAOI={}".format(AOI),
        "-POUTPUT_REFL={}".format(out_refl),
        "-POUTPUT_SUN_ZEN_ANG={}".format(out_sun_zenith),
        "-POUTPUT_MASK={}".format(out_mask),
        "-POUTPUT_BIO={}".format(out_bio)])

def elevation(gpt_path:str, in_mask:str, out_elev:str):
    """Running SNAP GPT graph to extract elevation data.

    Args:
        gpt_path (str): Path to SNAP GPT
        in_mask (str): Path to input mask (out_refl from s2_preprocessing)
        out_elev (str): Path to store the elevation data
    """

    subprocess.run([gpt_path, os.path.join(auxdata, "add_elevation.xml"),
        "-PINPUT_S2_MASK={}".format(in_mask),
        "-POUTPUT_SRTM_ELEV={}".format(out_elev)
        ])

def landcover(gpt_path:str, in_mask:str, out_lc:str):
    """Running SNAP GPT graph to extract LandCover data.

    Args:
        gpt_path (str): Path to SNAP GPT
        in_mask (str): Path to input mask (out_refl from s2_preprocessing)
        out_lc (str): Path to store the LandCover data
    """

    subprocess.run([gpt_path, os.path.join(auxdata, "add_landcover.xml"),
        "-PINPUT_S2_MASK={}".format(in_mask),
        "-POUTPUT_CCI_LC={}".format(out_lc)
        ])

def s3_preprocessing(gpt_path:str, S3_L2:str, AOI:str, out_obs_geom:str,
    out_mask:str, out_lst:str):
    """Preprocessing procedures for Sentinel 3 LST data.

    Args:
        gpt_path (str): Path to SNAP GPT
        S3_L2 (str): Path to Sentinel 3 image
        AOI (str): WKT geometry as string
        out_obs_geom (str): Path to store observation geometry file
        out_mask (str): Path to store mask file
        out_lst (str): Path to store LST file
    """

    subprocess.run([gpt_path, os.path.join(auxdata, "sentinel_3_preprocessing.xml"),
        "-PINPUT_S3_L2={}".format(S3_L2),
        "-PINPUT_AOI_WKT={}".format(AOI),
        "-POUTPUT_observation_geometry={}".format(out_obs_geom),
        "-POUTPUT_mask={}".format(out_mask),
        "-POUTPUT_LST={}".format(out_lst)])
