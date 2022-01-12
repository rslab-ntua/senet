import os
import pandas as pd
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt

EO_PRODUCT_TYPES = {
    "Sentinel-1": {
        "SLC": "SLC",
        "GRD": "GRD",
        "OCN": "OCN"
    },
    "Sentinel-2": {
        "S2MSI2A": "L2A",
        "S2MSI1C": "L1C",
        "S2MS2Ap": "L2A"
    },
    "Sentinel-3": {
        "SR_1_SRA___": "SR_1_SRA",
        "SR_1_SRA_A": "SR_1_SRA_A",
        "SR_1_SRA_BS": "SR_1_SRA_BS",
        "SR_2_LAN___": "SR_2_LAN",
        "OL_1_EFR___": "OL_1_EFR",
        "OL_1_ERR___": "OL_1_ERR",
        "OL_2_LFR___": "OL_2_LFR",
        "OL_2_LRR___": "OL_2_LRR",
        "SL_1_RBT___": "SL_1_RBT",
        "SL_2_LST___": "SL_2_LST",
        "SY_2_SYN___": "SSY_2_SYN___",
        "SY_2_V10___": "SY_2_V10___",
        "SY_2_VG1___": "SY_2_VG1___",
        "SY_2_VGP___": "SY_2_VGP___"
    }
}

EO_INSTRUMENTS = {
    "Sentinel-1": "SAR",
    "Sentinel-2": "MSI",
    "Sentinel-3": {
        "OLCI": "OLCI",
        "SLSTR": "SLSTR",
        "SRAL": "SRAL",
        "SYNERGY": "SYNERGY"
    }
}

def eodata_path_creator(data:pd.DataFrame):
    """Convert a DataFrame with the response from APIHUB to CreoDIAS paths. Works with Sentinel-1, 2, 3 (all instruments).
    Function builds paths as follows:
    S1: /eodata/platform/instrumentshortname/producttype/year/month/day/filename
    S2: /eodata/Sentinel-2/MSI/L2A/...
    S3: /eodata/Sentinel-3/instrument/producttype/...
    Args:
        data (pd.DataFrame): APIHUB response as DataFrame

    Returns:
        list: CreoDIAS paths
    """
    # Really ugly
    filenames = data['filename'].tolist()
    platform = data["platformname"].tolist()
    product = data["producttype"].tolist()
    year = [str(product_date.year) for product_date in data["ingestiondate"].tolist()]
    month = [f"{product_date.month:02d}" for product_date in data["ingestiondate"].tolist()]
    day = [f"{product_date.day:02d}" for product_date in data["ingestiondate"].tolist()]

    creodias_paths = []
    for i in range(len(data)):
        path = "/eodata"
        if platform[i] == "Sentinel-3":
            instrument = data["instrumentshortname"].iloc[[i]][0]
            instrument = EO_INSTRUMENTS[platform[i]][instrument]
        else:
            instrument = EO_INSTRUMENTS[platform[i]]

        path = os.path.join(path, platform[i], instrument, EO_PRODUCT_TYPES[platform[i]][product[i]], year[i], month[i], day[i], filenames[i])
        creodias_paths.append(path)
    
    return creodias_paths
    
def prepare_data_senet_S2(data:pd.DataFrame):
    """Cleans API response dataframe from Sentinel-2 L1C data.

    Args:
        data (pd.DataFrame): APIHUB response as DataFrame

    Raises:
        ValueError: If no Sentinel-2 L2A or L2Ap instances found

    Returns:
       pd.DataFrame: Cleaned DataFrame
    """

    unique_product_types = data["producttype"].unique()
    if ("S2MSI2A" or "S2MSI2Ap") not in unique_product_types:
        raise ValueError("Only Sentinel-2 L2A data are supported!")
    if "S2MSI1C" in unique_product_types:
        print ("Found Sentinel-2 L1C data. Only Sentinel-L2A data are supported!")
        print("Removing Sentinel-2 L1C data...")
        data = data[data.producttype != "S2MSI1C"]
        print("Done!")

    return data

def order_CREODIAS_L2A(data:pd.DataFrame):
    """TODO: MUST FIND A WAY TO ORDER OLDER (PAST 6 MONTHS) L2A DATA.

    Args:
        data (pd.DataFrame): [description]
    """
    pass

def get_data(area:str, start_date:str, end_date:str, username:str, password:str, platform:str = "Sentinel-2", **kwargs):
    """Get data information from ESA APIHUB.

    Args:
        area (str): Path to geometry file (geojson)
        start_date (str): Start date in YYYYMMDD format
        end_date (str): End date in YYYYMMDD format
        username (str): APIHUB username
        password (str): APIHUB password
        platform (str, optional): Platform name. Defaults to "Sentinel-2"
        **kwargs: Check https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/FullTextSearch?redirectedfrom=SciHubUserGuide.3FullTextSearch

    Returns:
        DataFrame: APIHUB response with the available data converted to DataFrame
    """
    api = SentinelAPI(f"{username}", f"{password}", "https://apihub.copernicus.eu/apihub/")
    footprint = geojson_to_wkt(read_geojson(area))
    products = api.query(footprint, date = (start_date, end_date), platformname = platform, **kwargs)
    products_df = api.to_dataframe(products)

    return products_df
    
"""
user = "alek.falagas"
password = "alekos1993"
geojson = "/home/tars/Desktop/RSLab/MAGO/Data/AOI/AOI.geojson"
start_date = "20210810"
end_date = "20210820"

data = get_data(geojson, start_date, end_date, user, password, producttype = "S2MSI2A")
print (data)
data = prepare_data_senet_S2(data)
creodias_paths = eodata_path_creator(data)
print(creodias_paths)

#data = get_data(geojson, start_date, end_date, user, password, platform = "Sentinel-1", producttype = "SLC")
#creodias_paths = eodata_path_creator(data)
#print(creodias_paths)
"""