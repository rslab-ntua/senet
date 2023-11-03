import os
import glob
import re

def extract_date(filename):
    # Use regular expression to extract the date in the format "YYYYMMDD"
    match = re.search(r'\d{8}', filename)
    if match:
        return match.group(0)
    else:
        return ''
    
search_s2_path = "/home/eouser/uth/cb-monthly/Sentinel-2/32SPF/"
search_s3_path = "/home/eouser/uth/cb-monthly/Sentinel-3/"
months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
years = ["2018", "2019", "2020", "2021", "2022"]

for year in years:
    for month in months:
        print("-------------")
        print (f"Date: {year}/{month}")
        print("Sentinel-2")
        search_pattern = f"*MSIL2A_{year}{month}*.SAFE"
        image_folders = glob.glob(os.path.join(search_s2_path, search_pattern))
        image_folders1 = sorted(image_folders, key=lambda x: extract_date(x))
        for image in image_folders1:
            print(image.split("/")[-1] + ",")
        print("Sentinel-3")
        search_pattern = f"*LST____{year}{month}*.SEN3"
        image_folders = glob.glob(os.path.join(search_s3_path, search_pattern))
        image_folders1 = sorted(image_folders, key=lambda x: extract_date(x))
        for image in image_folders1:
            print(image.split("/")[-1].split(".")[0] + ",")