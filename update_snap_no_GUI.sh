# Update SNAP and modules server-side

echo "Provide SNAP installation path:"
read -p "Is installation path /home/eouser/$USER/esa-snap/ and auxiliary path /home/eouser/$USER/.snap? [Y/n] " ANSWER
case "$ANSWER" in 
  [yY] | [yY][eE][sS])
    SNAP_INSTALLATION_FOLDER="/home/eouser/$USER/esa-snap"
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


echo "Updating SNAP and modules..."
.$SNAP_INSTALLATION_FOLDER"/bin/snap --nosplash --nogui --modules --update-all"
echo "Done"
