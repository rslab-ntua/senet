# Get and install SEN-ET plugin
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

URL="https://www.esa-sen4et.org/static/media/Sen-ET-plugin-v1.0.1.b41ae6c8.zip"
FILENAME=$(basename "$URL")
if [ ! -f $FILENAME ] 
then
  echo "Getting SEN-ET SNAP plugin..." 
  wget "$URL"
  echo "Done!"
fi

echo "Installing SEN-ET..."
unzip $FILENAME

# Setting plugin installation paths
XML_PATH="$SNAP_AUX_FOLDER/system/config/Modules"
JAR_PATH="$SNAP_AUX_FOLDER/system/modules"
# Make directories if not exist
if [ ! -d $XML_PATH ] 
then
  echo "Creating $XML_PATH directory..."
  mkdir $XML_PATH
fi

if [ ! -d $JAR_PATH ] 
then
  echo "Creating $JAR_PATH directory..."
  mkdir $JAR_PATH
fi

# Unzip netbeans to snap installation folder to install SEN-ET plugin
# Make a temporary folder to unzip nbm files
TMP_DIR="$PWD/.tmp" 
NBM_FILES=$(find "$PWD" -type f -name "*.nbm")
for nbm in $NBM_FILES
do
  echo "Unpacking $nbm..."
  unzip "$nbm" "netbeans/*" -d "$TMP_DIR"
done

cp -r "$TMP_DIR/netbeans/config/Modules/." "$XML_PATH"
cp -r "$TMP_DIR/netbeans/modules/." "$JAR_PATH"

echo "Removing $TMP_DIR directory..."
rm -rf $TMP_DIR
echo "Done."

#Python bundle installation
echo "Installing python bundle..."
BUNDLE_URL="https://senetfiles.blob.core.windows.net/files/sen-et-conda-Linux64.run"
BUNDLE_FILE=$(basename "$BUNDLE_URL")
if [ ! -f $SNAP_AUX_FOLDER/auxdata/$BUNDLE_FILE ]
then
  echo "Getting python bundle..."
  wget "$BUNDLE_URL" -P "$SNAP_AUX_FOLDER/auxdata/"
fi
chmod +x $SNAP_AUX_FOLDER/auxdata/$BUNDLE_FILE
(cd $SNAP_AUX_FOLDER/auxdata/; ./$BUNDLE_FILE)

echo "Installation finished."