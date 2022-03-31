# senet
Energy Balance model approach for irrigation (SEN-ET SNAP plugin).

## Installation

### Install ESA SNAP

For the installation of ESA SNAP run the automated script (`install_snap.sh`) for downloading and installing the official Linux installer from the official ESA repository. To install SNAP
run the following commands:

```bash
$chmod +x install_snap.sh
$./install_snap.sh
```

:warning: Do not install SNAP to default option (/home/USER/snap) and install it in a different folder (e.g /home/USER/esa-snap) to avoid facing problems with Ubuntu snap.

### Install SEN-ET SNAP plugin

Since there is no official support of SNAP to install plugins through CLI, `install_senet.sh` script was developed for the installation of SEN-ET plugin. The script downloads SEN-ET plugin, and sets the enviroment for the installation of the netbeans (`*.nbm`) SEN-ET modules. To install SEN-ET a complete installation of ESA SNAP is required and user must provide a full SNAP installation path (e.g /home/USER/esa-snap) and also SNAP installation auxiliary path (e.g /home/USER/.snap). To install SEN-ET run the following commands:

```bash
$chmod +x install_senet.sh
$./install_senet.sh
```

### SNAPPY permanent installation

To configure SNAPPY permanently in a Python enviroment use `snappy_conf_perm.sh`. The shell script input are the complete installation path of SNAP and the python path.

```bash
$chmod +x snappy_conf_perm.sh
$./snappy_conf_perm.sh
```

### Install ESA CCI Land Cover Map

Download and install ESA CCI Land Cover Map to ESA-SNAP with `install_CCI_LC.sh` script. The shell script input is the complete installation path of SNAP.

```bash
$chmod +x install_CCI_LC.sh
$./install_CCI_LC.sh
```

### Install Python GDAL

Use `install_gdal.sh` for a complete installation of GDAL python bindings.

```bash
$chmod +x install_gdal.sh
$./install_gdal.sh
```

### Install ECMWF CDS API Key

The Climate Data Store Application Program Interface is a service providing programmatic access to CDS data. Use `install_CDS_key.sh` to install the CDS API key.

```bash
$chmod +x install_CDS_key.sh
$./install_CDS_key.sh
```

:warning: An CDS Copernicus climate account must be provided in order to have the API key. Create a new account [here](https://cds.climate.copernicus.eu/cdsapp#!/home).

### Update server SNAP

Since no UI is provided to update SNAP use `update_snap_no_GUI.sh` to get the latest version of ESA SNAP.

```bash
$chmod +x update_snap_no_GUI.sh
$./update_snap_no_GUI.sh
```

## Python Pipeline

The following section analyses step by step the complete Python pipeline in order to acquire daily evapotranspiration. 

| Python Method Index                                                                                       | Operation Type     |
------------------------------------------------------------------------------------------------------------|--------------------|
| [Get Data](#get-data)                                                                                     | Python Method      |
| [Sentinel-2 preprocessing graph](#sentinel-2-preprocessing-graph)                                         | GPF SNAP Graph     |
| [Add elevation graph](#add-elevation-graph)                                                               | GPF SNAP Graph     |
| [Add landcover graph](#add-landcover-graph)                                                               | GPF SNAP Graph     |
| [Estimate leaf reflectance and transmittance](#estimate-leaf-reflectance-and-transmittance)               | Python Method      |
| [Estimate fraction of green vegetation](#estimate-fraction-of-green-vegetation)                           | Python Method      |
| [Produce maps of vegetation structural parameters](#produce-maps-of-vegetation-structural-parameters)     | Python Method      |
| [Estimate aerodynamic roughness](#estimate-aerodynamic-roughness)                                         | Python Method      |
| [Sentinel-3 pre-processing graph](#sentinel-3-pre-processing-graph)                                       | GPF SNAP Graph     |
| [Warp to template](#warp-to-template)                                                                     | Python Method      |
| [Sharpen LST](#sharpen-lst)                                                                               | Python Method      |
| [Download ECMWF ERA5 reanalysis data](#download-ecmwf-era5-reanalysis-data)                               | Python Method      |
| [Prepare ERA5 reanalysis data](#prepare-era5-reanalysis-data)                                             | Python Method      |
| [Estimate longwave irradiance](#estimate-longwave-irradiance)                                             | Python Method      |
| [Estimate net shortwave radiation](#estimate-net-shortwave-radiation)                                     | Python Method      |
| [Estimate land surface energy fluxes](#estimate-land-surface-energy-fluxes)                               | Python Method      |
| [Estimate daily evapotranspiration](#estimate-daily-evapotranspiration)                                   | Python Method      |

### Get data

At first a Sentinel-2 L2A multispectral image and a Sentinel-3 LST thermal image at the same date have to be selected. The images currently are found  from Copernicus Open Access Hub, given an area of interest (AOI) and a date range.

:warning: Note that an ESA APIHUB account must be used for searching satellite data and also, user and password variables must be changed inside the code. Create a new account [here](https://scihub.copernicus.eu/dhus/#/self-registration).

See the example bellow:

```python
import os
import getpass
import geopandas
import pyproj
from datetime import datetime, timedelta

from get_creodias import get_data, prepare_data_senet_S2 eodata_path_creator
from sentinels import sentinel2, sentinel3

# All ROI must be in WGS84
wgs_crs = pyproj.crs.CRS("epsg:4326")

USER = getpass.getuser()

meteo_datapath = "/home/eouser/uth/Cap_Bon/Meteo/"

AOI_path = "/home/eouser/uth/Cap_Bon/AOI/AOI_Cap_Bon.geojson"
AOI = geopandas.read_file(AOI_path)
CRS = AOI.crs

if CRS != wgs_crs:
    AOI = AOI.to_crs(wgs_crs.to_epsg())

WKT_GEOM = AOI.geometry[0]

user = "guest"
password = "guest"
start_date = "20210810"
end_date = "20210820"
data = get_data(AOI_path, start_date, end_date, user, password, producttype = "S2MSI2A")
data = prepare_data_senet_S2(data)
creodias_paths = eodata_path_creator(data)

# From all available images select the first
s2_path, s2_name = os.path.split(creodias_paths[0])
print(s2_path, s2_name)

s2 = sentinel2(s2_path, s2_name)
s2.getmetadata()

# Now select an available S3 image
start_date = s2.date
end_date = s2.date + timedelta(days=1)
data = get_data(AOI_path, start_date, end_date, user, password, platform = "Sentinel-3", producttype = "SL_2_LST___")
creodias_paths = eodata_path_creator(data)

for path in creodias_paths:
    # Again select the first image
    s3_path, s3_name = os.path.split(path)
    s3 = sentinel3(s3_path, s3_name)
    s3.getmetadata()

    if s3.date == s2.date:
        break

# Because the user has no permission to write make a new directory inside the user with the selected image name
home = "/home/eouser/uth"

if not os.path.exists(os.path.join(home, "Sentinel-2")):
    os.mkdir(os.path.join(home, "Sentinel-2"))
if not os.path.exists(os.path.join(home, "Sentinel-2", s2.tile_id)):
    os.mkdir(os.path.join(home, "Sentinel-2", s2.tile_id))
if not os.path.exists(os.path.join(home, "Sentinel-2", s2.tile_id, s2.name)):
    os.mkdir(os.path.join(home, "Sentinel-2", s2.tile_id, s2.name))

s2_savepath = os.path.join(home, "Sentinel-2", s2.tile_id)

if not os.path.exists(os.path.join(home, "Sentinel-3")):
    os.mkdir(os.path.join(home, "Sentinel-3"))
if not os.path.exists(os.path.join(home, "Sentinel-3", s3.name)):
    os.mkdir(os.path.join(home, "Sentinel-3", s3.name))

s3_savepath = os.path.join(home, "Sentinel-3")
```

### Sentinel-2 preprocessing graph

This graph resamples the L2A Sentinel-2 scene to 20 m, subsets required bands and saves them as individual products and estimates biophysical parameters from the refectance bands. This step creates a product containing the 20 m reflectance bands (B2, B3,
B4, B5, B6, B7, B8A, B11, B12), a product containing the scene's sun zenith angle
band (sun_zenith), a product containing cloud mask derived from scene's quality flags and
a product containing biophysical parameters (LAI, FAPAR, Fcover, Cab, Cw). See the example bellow:

```python
import os
import subprocess

subprocess.run([f"/home/eouser/{USER}/esa-snap/bin/gpt", "./auxdata/sentinel_2_preprocessing.xml",
"-PINPUT_S2_L2A={}".format(os.path.join(s2_path, s2_name, "MTD_MSIL2A.xml")),
"-PAOI={}".format(WKT_GEOM),
"-POUTPUT_REFL={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_REFL".format(s2.tile_id, s2.str_datetime))),
"-POUTPUT_SUN_ZEN_ANG={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_SUN-ZEN-ANG".format(s2.tile_id, s2.str_datetime))),
"-POUTPUT_MASK={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_MASK".format(s2.tile_id, s2.str_datetime))),
"-POUTPUT_BIO={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_BIO".format(s2.tile_id, s2.str_datetime)))
])
```

### Add elevation graph

This graph creates a high resolution digital elevation model (DEM) for the given L2A Sentinel-2 scene. See the example bellow:

```python
import os
import subprocess

subprocess.run([f"/home/eouser/{USER}/esa-snap/bin/gpt", "./auxdata/add_elevation.xml",
"-PINPUT_S2_MASK={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))),
"-POUTPUT_SRTM_ELEV={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_ELEV".format(s2.tile_id, s2.str_datetime)))
])
```

### Add landcover graph

This graph creates A land-cover map for the given Sentinel-2 scene using the ESA CCI Land Cover 2015 map. ESA CCI Land Cover 2015 map is already downloaded with SNAP. See the example bellow:

```python
import os
import subprocess

subprocess.run([f"/home/eouser/{USER}/esa-snap/bin/gpt", "./auxdata/add_landcover.xml",
"-PINPUT_S2_MASK={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_MASK.dim".format(s2.tile_id, s2.str_datetime))),
"-POUTPUT_CCI_LC={}".format(os.path.join(s2_savepath, s2_name, "{}_{}_LC".format(s2.tile_id, s2.str_datetime)))
])
```

### Estimate leaf reflectance and transmittance

This step estimates leaf reflectance and transmittance based on plant chlorophyl and water content. The input of the method is the
plant biophysical properties product - output of [Sentinel-2 preprocessing graph](#sentinel-2-preprocessing-graph). See the example bellow:

```python
import os
from core.leaf_spectra import leaf_spectra

biophysical_file = os.path.join(s2_savepath, s2_name, "AUX_DATA", "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
output = os.path.join(s2_savepath, s2_name, "{}_{}_LEAF-REFL-TRAN.dim".format(s2.tile_id, s2.str_datetime))
leaf_spectra(biophysical_file, output)
```

### Estimate fraction of green vegetation

This step estimates the fraction of vegetation which is green based on the leaf area index (LAI), fraction of absorbed photosynthetically active radiation (FAPAR) and sun zenith angle bands (outputs of [Sentinel-2 preprocessing graph](#sentinel-2-preprocessing-graph)).
Requires from user the minimum fraction of vegetation which is green.
See the example bellow:

```python
import os
from core.frac_green import fraction_green

sun_zenith_angle = os.path.join(s2_savepath, s2_name, "{}_{}_SUN-ZEN-ANG.dim".format(s2.tile_id, s2.str_datetime))
biophysical_file = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
output = os.path.join(s2_savepath, s2_name, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
minfc = 0.01
fraction_green(sun_zenith_angle, biophysical_file, minfc, output)
```

### Produce maps of vegetation structural parameters

This step produces maps of vegetation structural parameters required for TSEB model, based on a land cover map and a look-up table (in auxdata folder). See example bellow:

```python
import os
from core.structural_params import str_parameters

lcmap = os.path.join(s2_savepath, s2_name, "{}_{}_LC.dim".format(s2.tile_id, s2.str_datetime))
biophysical_file = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
fvg_map = os.path.join(s2_savepath, s2_name, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
landcover_band = "land_cover_CCILandCover-2015"
produce_vh = True
produce_fc = True
produce_chwr = True
produce_lw = True
produce_lid = True
produce_igbp = True
output = os.path.join(s2_savepath, s2_name, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
str_parameters(lcmap, biophysical_file, fvg_map, landcover_band,
    produce_vh, produce_fc, produce_chwr, produce_lw, produce_lid,
    produce_igbp, output)
```

### Estimate aerodynamic roughness

This step estimates aerodynamic roughness length for momentum transport (m) and
zero-plane displacement height (m) based on the leaf area index (LAI) and the maps of
vegetation structural parameters. See example bellow:

```python
import os
from core.aerodynamic_roughness import aerodynamic_roughness

biophysical_file = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
param_file = os.path.join(s2_savepath, s2_name, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
output = os.path.join(s2_savepath, s2_name, "{}_{}_AERO-ROUGH.dim".format(s2.tile_id, s2.str_datetime))
aerodynamic_roughness(biophysical_file, param_file, output)
```

### Sentinel-3 pre-processing graph

This graph reprojects the downloaded L2A Sentinel-3 scene to the given AOI subsets required bands and saves them as individual products.

```python
subprocess.run([f"/home/{USER}/esa-snap/bin/gpt", "./auxdata/sentinel_3_preprocessing.xml",
    "-PINPUT_S3_L2={}".format(os.path.join(s3_path, s3_name)),
    "-PINPUT_AOI_WKT={}".format(WKT_GEOM),
    "-POUTPUT_observation_geometry={}".format(os.path.join(s3_savepath, s3_name, "LST_OBS-GEOM.dim")),
    "-POUTPUT_mask={}".format(os.path.join(s3_savepath, s3_name, "LST_MASK.dim")),
    "-POUTPUT_LST={}".format(os.path.join(s3_savepath, s3_name, "LST_data.dim"))
    ])
```

### Warp to template

This operator reprojects, resamples and subsets a source image to a template image using GDAL Warp.

```python
import os
from core.warp_to_template import warp

source_image = os.path.join(s3_savepath, s3_name, "LST_OBS-GEOM.dim")
temp_image = os.path.join(s2_savepath, s2_name, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))
output_image = os.path.join(s3_savepath, s3_name, "LST_OBS-GEOM-REPROJ.dim")
warp(source_image, temp_image, output_image)
```

### Sharpen LST
This step uses the Python implementation of the Data Mining Sharpener. It can be used to sharpen SLSTR Land Surface Temperature to Sentinel-2 spatial resolution.

```python
s2_refl = os.path.join(s2_savepath, s2_name, "{}_{}_REFL.dim".format(s2.tile_id, s2.str_datetime))
s3_lst = os.path.join(s3_savepath, s3_name, "LST_data.dim")
dem = os.path.join(s2_savepath, s2_name, "{}_{}_ELEV.dim".format(s2.tile_id, s2.str_datetime))
geom = os.path.join(s3_savepath, s3_name, "LST_OBS-GEOM-REPROJ.dim")
lst_mask = os.path.join(s3_savepath, s3_name, "LST_MASK.dim")
datetime_utc_str = s3.datetime.strftime("%Y-%m-%d %H:%M")
datetime_utc = datetime.strptime(datetime_utc_str, "%Y-%m-%d %H:%M")
output = os.path.join(s3_savepath, s3_name, "LST_SHARP.dim")
parallel_jobs = 3
moving_window_size = 30
sharpen(s2_refl, s3_lst, dem, geom, lst_mask, datetime_utc, output, moving_window_size = moving_window_size, parallel_jobs = parallel_jobs)
```

### Download ECMWF ERA5 reanalysis data

This operators downloads ECMWF ERA5 reanalysis data from the Climate Data Store (CDS). Note that this requires CDS registration and the CDS key located in the correct path. See the example bellow:

```python
import os
import math
from core.ecmwf_data_download import get

# N/W/S/E over a slightly larger area to contain all the AOI
N = math.ceil(AOI.bounds.maxy[0])
E = math.ceil(AOI.bounds.maxx[0])
W = math.floor(AOI.bounds.minx[0])
S = math.floor(AOI.bounds.miny[0])
CDS_AOI = "{}/{}/{}/{}".format(N, W, S, E)
start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
down_path = os.path.join(meteo_datapath, "meteo_{}_{}.nc".format(start_date, end_date))
get(CDS_AOI, start_date, end_date, down_path)
```

### Prepare ERA5 reanalysis data

This step prepares ERA5 reanalysis surface meteorological data based on the ECMWF ERA5 reanalysis data and the high resolution DEM. See the example bellow:

```python
import os
from timezone import get_offset
from core.ecmwf_data_preparation import prepare

centroid = AOI.geometry[0].centroid
coordinates = {"lat": centroid.y, "lng": centroid.x, "date_time": s2.datetime}
offset = get_offset(**coordinates)
elevation_map = os.path.join(s2_savepath, s2_name, "{}_{}_ELEV.dim".format(s2.tile_id, s2.str_datetime))
ecmwf_data = os.path.join(meteo_datapath, "meteo_{}_{}.nc".format(start_date, end_date))
date_time_utc = s2.datetime
time_zone = offset
output = os.path.join(meteo_datapath, "meteo_{}_{}_PROC".format(start_date, end_date))
prepare(elevation_map, ecmwf_data, date_time_utc, time_zone, output)
```

### Estimate longwave irradiance

This step estimates atmosphere longwave irradiance (W/m2) based on meteorological inputs. See the example bellow:

```python
import os
from datetime import datetime, timedelta
from core.longwave_irradiance import longwave_irradiance

start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
meteo = os.path.join(meteo_datapath, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
output = os.path.join(meteo_datapath, "meteo_{}_LONG_IRRAD.dim".format(s2.date))
longwave_irradiance(meteo, output)
```

### Estimate net shortwave radiation

This step estimates net shortwave radiation based on meteorological and biophysical inputs. See the example bellow:

```python
import os
from datetime import datetime, timedelta
from core.net_shortwave_radiation import net_shortwave_radiation

start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
lsp_product = os.path.join(s2_savepath, s2_name, "{}_{}_LEAF-REFL-TRAN.dim".format(s2.tile_id, s2.str_datetime))
lai_product = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
csp_product = os.path.join(s2_savepath, s2_name, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
mi_product = os.path.join(meteo_datapath, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
sza_product =  os.path.join(s3_savepath, s3_name, "LST_OBS-GEON-REPROJ.dim")
output_file = os.path.join(s2_savepath, s2_name, "{}_{}_NET-RAD.dim".format(s2.tile_id, s2.str_datetime))
net_shortwave_radiation(lsp_product, lai_product, csp_product, mi_product, sza_product, output_file)
```

### Estimate land surface energy fluxes

This step estimates land surface energy fluxes (latent, sensible, ground heat and net radiation) using One-Source Energy Balance model for bare soil pixels and Two-Source Energy Balance model for vegetated pixels. See the example bellow:

```python
import os
from datetime import datetime, timedelta
from core.energy_fluxes import energy_fluxes

start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
lst = os.path.join(s3_savepath, s3_name, "LST_SHARP.dim")
lst_vza = os.path.join(s3_savepath, s3_name, "LST_OBS-GEON-REPROJ.dim")
lai = os.path.join(s2_savepath, s2_name, "{}_{}_BIO.dim".format(s2.tile_id, s2.str_datetime))
csp =  os.path.join(s2_savepath, s2_name, "{}_{}_STR-PARAM.dim".format(s2.tile_id, s2.str_datetime))
fgv = os.path.join(s2_savepath, s2_name, "{}_{}_FV.dim".format(s2.tile_id, s2.str_datetime))
ar = os.path.join(s2_savepath, s2_name, "{}_{}_AERO-ROUGH.dim".format(s2.tile_id, s2.str_datetime))
mi = os.path.join(meteo_datapath, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
nsr = os.path.join(s2_savepath, s2_name, "{}_{}_NET-RAD.dim".format(s2.tile_id, s2.str_datetime))
li = os.path.join(meteo_datapath, "meteo_{}_LONG_IRRAD.dim".format(s2.date))
mask = os.path.join(s2_savepath, s2_name, "{}_{}_MASK.dim".format(s2.tile_id, s2.str_datetime))
output_file = os.path.join(s2_savepath, s2_name, "{}_{}_EN-FLUX.dim".format(s2.tile_id, s2.str_datetime))
energy_fluxes(lst, lst_vza, lai, csp, fgv, ar, mi, nsr, li, mask, output_file)
```

### Estimate daily evapotranspiration

This step estimates daily evapotranspiration by extrapolating instantaneous latent heat flux using daily solar irradiance. See the example bellow:

```python
import os
from datetime import datetime, timedelta
from core.daily_evapotranspiration import daily_evapotranspiration

start_date = str(s2.date - timedelta(days = 1))
end_date = str(s2.date + timedelta(days = 1))
ief_file = os.path.join(s2_savepath, s2_name, "{}_{}_EN-FLUX.dim".format(s2.tile_id, s2.str_datetime))
mi_file = os.path.join(meteo_datapath, "meteo_{}_{}_PROC.dim".format(start_date, end_date))
output_file = os.path.join(s2_savepath, s2_name, "{}_{}_EVAP.dim".format(s2.tile_id, s2.str_datetime))

daily_evapotranspiration(ief_file, mi_file, output_file)
```