# Get and install ESA-CCI Maps
# File created for MAGO Project
# Alekos Falagas (alek.falagas@gmail.com)

echo "Provide SNAP installation path:"
read -p "Is installation path /home/$USER/esa-snap/ and auxiliary path /home/$USER/.snap? [Y/n] " ANSWER
case "$ANSWER" in 
  [yY] | [yY][eE][sS])
    SNAP_INSTALLATION_FOLDER="/home/$USER/esa-snap/"
    SNAP_AUX_FOLDER="/home/$USER/.snap"
    ;;
  [nN] | [nN][oO])
    read -p "Provide installation path: " SNAP_INSTALLATION_FOLDER
    read -p "Provide auxiliary path: " SNAP_AUX_FOLDER
    ;;
  *)
    echo "Error: Invalid option."
    exit 1
    ;;
esac

# Check if folders exist
if [ ! -d $SNAP_INSTALLATION_FOLDER ] 
then
  echo "Error: Directory $SNAP_INSTALLATION_FOLDER does not exists."
  exit 2
fi

if [ ! -d $SNAP_AUX_FOLDER ] 
then
  echo "Error: Directory $SNAP_AUX_FOLDER does not exists."
  exit 2
fi

# NO NEED FOR ROOT ACCESS is required for the instalation
FTP="ftp://geo10.elie.ucl.ac.be/CCI/LandCover/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2015-v2.0.7.zip" 

CCI=$(basename "$FTP")

if [ ! -f $CCI ] 
then
echo "Getting $FTP..."
wget $FTP
echo "Done!"
else
echo "$FTP already exists..."
fi

# Making the directories for the installation
CCI_INSTALLATION_FOLDER="$SNAP_AUX_FOLDER/auxdata/LandCover/CCILandCover-2015/"
FILE="$CCI_INSTALLATION_FOLDER/$CCI"
echo "Installing $CCI under $CCI_INSTALLATION_FOLDER..."
if [ ! -d $CCI_INSTALLATION_FOLDER ]
then
mkdir $CCI_INSTALLATION_FOLDER
if [ ! -f $FILE ]
then
cp $CCI $CCI_INSTALLATION_FOLDER
fi
else
if [ ! -f $FILE ]
then
cp $CCI $CCI_INSTALLATION_FOLDER
fi
fi

echo "Removing downloaded files..."
rm $CCI
echo "Done!"

echo "Installation finished!"