import os
import shutil

S2_SAVEPATH = "/home/eouser/uth/Benchmarking_Senet/Sentinel-2/32SPF/S2B_MSIL2A_20220808T095559_N0400_R122_T32SPF_20220808T123856.SAFE"
S3_SAVEPATH = "/home/eouser/uth/Benchmarking_Senet/Sentinel-3/S3A_SL_2_LST____20220808T094230_20220808T094530_20220809T191445_0179_088_250_2340_PS1_O_NT_004.SEN3"
# Removing data to free disk space
for file in os.listdir(S2_SAVEPATH):
    if not (file.endswith("EVAP.dim") or file.endswith("EVAP.data")):
        if file.endswith(".data"):
            shutil.rmtree(os.path.join(S2_SAVEPATH, file))
        else:
            os.remove(os.path.join(S2_SAVEPATH, file))

for file in os.listdir(S3_SAVEPATH):
    if file.endswith(".data"):
        shutil.rmtree(os.path.join(S3_SAVEPATH, file))
    else:
        os.remove(os.path.join(S3_SAVEPATH, file))