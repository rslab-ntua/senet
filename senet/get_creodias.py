import os
import pandas as pd
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from creodias_finder import query
from datetime import datetime

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
    
    creodias_paths = []
    for i in range(len(data)):
        path = "/eodata"
        if platform[i] == "Sentinel-3":
            instrument = data["instrumentshortname"].iloc[[i]][0]
            instrument = EO_INSTRUMENTS[platform[i]][instrument]
        else:
            instrument = EO_INSTRUMENTS[platform[i]]

        year = str(data["beginposition"].iloc[[i]][0].year)
        month = "{:02d}".format(data["beginposition"].iloc[[i]][0].month)
        day = "{:02d}".format(data["beginposition"].iloc[[i]][0].day)

        path = os.path.join(path, platform[i], instrument, EO_PRODUCT_TYPES[platform[i]][product[i]], year, month, day, filenames[i])
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

def get_data_DIAS(area:str, start_date:str, end_date:str, platform:str = "Sentinel2", **kwargs):
    """Query the Copernicus Data Space Ecosystem (CDSE) OpenSearch service for available products.
    - For Sentinel-2 catalog attributes: https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/describe.xml
    - For Sentinel-3 catalog attributes: https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel3/describe.xml
    Args:
        area (str): WKT geometry of the AOI.
        start_date (str): Start date in YYYYMMDD format.
        end_date (str): Start date in YYYYMMDD format.
        platform (str, optional): Platform name (like Sentinel2 or Sentinel3). Defaults to "Sentinel2".

    Returns:
        list: List of available products in CreoDIAS based on the query.
    """
    data = []
    results = query.query(
        platform,
        geometry=area,
        start_date=datetime(int(start_date[:4]), int(start_date[4:6]), int(start_date[6:])),
        end_date=datetime(int(end_date[:4]), int(end_date[4:6]), int(end_date[6:])),
        **kwargs)
    for key in results:
        data.append(results[key]["properties"]["productIdentifier"])

    return data

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
    if products_df.empty:
        raise ValueError("ESA SciHUB returned empty request! This is either a bad request or there are no data available in the selected date range!")
    
    return products_df