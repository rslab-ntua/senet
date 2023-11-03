import os
import glob
import rasterio
import numpy

search_path = "/home/eouser/uth/cb-monthly/Sentinel-2/32SPF/"
destintation_path = "/home/eouser/uth/cb-monthly/Gtiff/"

months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
years = ["2018", "2019", "2020", "2021", "2022"]

for year in years:
    for month in months:
        print("-------------")
        print (f"Date: {year}/{month}")
        search_pattern = f"*{year}{month}*.SAFE"
        image_folders = glob.glob(os.path.join(search_path, search_pattern))
        print (image_folders)

        if len(image_folders) == 0:
            print(f"No data found for {year}/{month}")
        elif len(image_folders) == 1:
            image_path = glob.glob(f"{image_folders[0]}/**/daily_evapotranspiration.img", recursive = True)[0]
            src = rasterio.open(image_path)
            new_file = os.path.join(destintation_path, f"{year}_{month}.tif")
            metadata = src.meta.copy()
            metadata.update(driver = "Gtiff")
            with rasterio.open(new_file, "w", **metadata) as dst:
                dst.write(src.read())
        else:
            image_paths = []
            for image in image_folders:
                print(glob.glob(f"{image}/**/daily_evapotranspiration.img", recursive = True))
                image_paths.append(glob.glob(f"{image}/**/daily_evapotranspiration.img", recursive = True)[0])
            
            all_data = []
            for image in image_paths:
                src = rasterio.open(image)
                data = src.read()
                all_data.append(data)
            average = numpy.nanmean(all_data, axis = 0)
            new_file = os.path.join(destintation_path, f"{year}_{month}.tif")
            metadata = src.meta.copy()
            metadata.update(driver = "Gtiff")
            with rasterio.open(new_file, "w", **metadata) as dst:
                dst.write(average)