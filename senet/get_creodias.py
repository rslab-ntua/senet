import os
import pandas as pd
from sentinelsat import read_geojson, geojson_to_wkt
from creodias_finder import query
from datetime import datetime
import requests

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

CDS_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name"


def get_data_DIAS(area: str, start_date: str, end_date: str, platform: str = "Sentinel2", **kwargs):
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


def get_data(area: str, start_date: str, end_date: str, platform: str, product_type: str, max_cloud_cover=100):
    """Get data information from Copernicus dataspace.

    Args:
        area (str): Path to geometry file (geojson)
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        platform (str): Platform name. Example: "SENTINEL-2"
        product_type (str): product name. Example "S2MSI2A"
        max_cloud_cover (int, optional): maximum cloud cover in percentage to filter images. Default to 100.
    Returns:
        DataFrame: APIHUB response with the available data converted to DataFrame
    """
    footprint = geojson_to_wkt(read_geojson(area))
    query_products = (f"{CDS_URL} eq '{platform}' and OData.CSC.Intersects(area=geography'SRID=4326;{footprint}') and"
                      f" ContentDate/Start gt {start_date}T00:00:00.000Z and "
                      f"ContentDate/Start lt {end_date}T00:00:00.000Z and "
                      "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and "
                      f"att/OData/CSC.StringAttribute/Value eq '{product_type}')")
    # For Sentinel-3 data: when max cloud cover is given in the request, the query always returns an empty json
    if max_cloud_cover < 100:
        query_products += (f" and Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and "
                           f"att/OData.CSC.DoubleAttribute/Value le {max_cloud_cover})")

    query_products += "&$top=1000"

    products = requests.get(query_products).json()
    if 'value' not in products.keys():
        raise ValueError("Bad request")
    products_df = pd.DataFrame.from_dict(products['value'])
    if products_df.empty:
        raise ValueError("Copernicus dataspace returned empty request! There are no "
                         "data available in the selected date range!")

    return products_df
