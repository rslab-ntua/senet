1. Install SNAP ESA and SEN-ET plugin to TARS and run an experiment.
#BUG :bug: GraphBuilder - Only on UI!

2. Try to write a bash script or a python script or a dockerfile to install SNAP and senet.
DONE with latest update (8/11) and bash scripts (install_snap.sh and install_senet.sh)

Installation can be done through command line.
Installation process:

    $wget https://download.esa.int/step/snap/8.0/installers/esa-snap_all_unix_8_0.sh
    $chmod +x esa-snap_all_unix_8_0.sh
    $./esa-snap_all_unix_8_0.sh

Getting SEN-ET plugin

    $wget https://www.esa-sen4et.org/static/media/Sen-ET-plugin-v1.0.1.b41ae6c8.zip
    $unzip Sen-ET-plugin-v1.0.1.b41ae6c8.zip

Did not manage currently to install the plugin through CLI.
Possible solution (DOES NOT WORK SO FAR):
    
    $cp -R /home/tars/Desktop/RSLab/MAGO/ET/Sen-ET-plugin-v1.0.1.b41ae6c8/Sen-ET-plugin-1.0.1/nbm/ /home/tars/.snap/system 
    $unzip /home/case/Desktop/RSLab/MAGO/ET/Sen-ET-plugin-v1.0.1.b41ae6c8/Sen-ET-plugin-1.0.1/nbm/* netbeans/* home/case/.snap/system

WORKS MAKE NEW SCRIPT (BASH OR PYTHON) -> Latest Update (08/11 DONE)
OR (NEEDS DEBUGGING :bug:)

    $/home/case/esa-snap/bin/snap --nosplash --nogui --modules --install /home/case/Desktop/RSLab/MAGO/ET/Sen-ET-plugin-1.0.1/nbm/aerodynamicRoughness-1.0.1.nbm

SNAPPY Install (WORKS)

    $./esa-snap/bin/snappy-conf /usr/bin/python3

Other possible solution is through docker
Get https://hub.docker.com/r/mundialis/esa-snap
Install somehow plugin and serve

Docker is still an option for setting the plugin

3. In case 2 is hard, write all the code from scratch:

    1. https://github.com/DHI-GRAS/senEtSnapSta
    2. https://github.com/DHI-GRAS/pyTSEB
    3. https://github.com/DHI-GRAS/sen-et-snap-scripts

NO NEED FOR THIS

4. ROAD TO CREODIAS

4.1 PIPELINE with SNAP or SNAPPY

    1. Download-GET Sentinel data (SOLVED WITH CREODIAS account, locally we run some experiments on our data)
    
    2. Sentinel-2 preprocessing graph (WORKED! BUT SOME ISSUES WITH BIOPHYSICAL OPERATOR AUXDATA OCCURED. STILL THE DELIVERED RESULTS)
    
    3. Add elevation graph (DONE!)
    
    4. Add landcover graph (DONE!) (#BUG traced at step 4 and fixed.)
    
    5. Estimate leaf reflectance and transmittance (DONE WITH PYTHON IMPLEMENTATION OF leaf_spectra.py)
    
    6. Estimate fraction of green vegetation (Problem with GDAL python bindings from PyTSEB)-> FIXED WITH install_gdal.sh (UPDATE 19/11/2021)
    
    7. Produce maps of vegetation structural parameters
    PYTHON ERROR:
        Traceback (most recent call last):
        File "run_senet.py", line 83, in <module> produce_igbp, output)
        File "/mnt/a202d601-6efc-44f7-8408-f8322b69b445/RSLab/Github/senet/senet/plugin/structural_params.py", line 71, in str_parameters
        lc_index = lut["landcover_class"].index(lc_class)
        ValueError: 1e-04 is not in list
        - FIXED BY TRACING A #BUG AT LANDCOVER GRAPH PROCESSING
    
    8. Estimate aerodynamic roughness (DONE!)
    
    9. Sentinel-3 pre-processing graph (DONE!) FIXED SOME #BUGS in *.xml GRAPH FILE
    
    10. Warp to template (Need to run an example) -> DONE!
    
    11. Sharpen LST (REALLY HUNGRY PROCESS!) -> DONE!
    
    12. Download ECMWF ERA5 reanalysis data -> DONE!
    
    13. Prepare ERA5 reanalysis data -> DONE!
    
    14. Estimate longwave irradiance -> DONE!
    
    15. Estimate net shortwave radiation -> DONE!
    
    16. Estimate land surface energy fluxes -> DONE!
    
    17. Estimate daily evapotranspiration -> DONE!!!

4.2 WATCH THIS (https://www.youtube.com/watch?v=PiU68g3WRIY&t=2051s)