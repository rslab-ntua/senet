# senet
Energy Balance model approach for irrigation (SEN-ET SNAP plugin).

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
