
import os
import logging
import xml.etree.ElementTree as Etree
import lxml.etree as lEtree
import fnmatch
import datetime
import pyproj
import urllib

# Define a lambda function to convert dates
convert = lambda x: datetime.datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%fZ')

class sentinel2():
    """A Sentinel 2 image."""
    
    def __init__(self, path, name):
        """ A Sentinel 2 image.
        Args:
            path (str, path-like): Path to image
            name (str): Name of the file
        """
        self.path = path
        self.name = name
        self.md_file = None
        self.tile_md_file = None
        self.satellite = None
        self.datetime = None
        self.date = None
        self.time = None
        self.str_datetime = None
        self.gml_coordinates = None
        self.cloud_cover = None
        self.processing_level = None
        self.tile_id = None
        self.crs = None

    def getmetadata(self):
        """Searching for metadata (XML) files.
        """
        for (dirpath, dirnames, filenames) in os.walk(os.path.join(self.path, self.name)):
            for file in filenames:
                if file.startswith("MTD_MSI"):
                    self.md_file = file
                    XML = self._readXML(dirpath, file)
                    self._parseGeneralMetadata(XML)
                elif file.startswith("MTD_TL"):
                    self.tile_md_file = file
                    XML = self._readXML(dirpath, file)
                    self._parseTileMetadata(XML)

    def _readXML(self, path:str, file:str):
        """Reads XML file.

        Args:
            path (str): Path to file
            file (str): Name of the file plus extention

        Returns:
            Etree.Element: XML opened file
        """
        tree = Etree.parse(os.path.join(path, file))
        root = tree.getroot()

        return root

    def _parseGeneralMetadata(self, root):
        """Parsing general S2 metadata from eTree.Element type object.

        Args:
            root (eTree.Element): S2 metadata from eTree.Element type object
        """
        self.satellite = root.findall(".//SPACECRAFT_NAME")[0].text
        self.str_datetime = self.name[11:26]
        self.datetime = convert(root.findall(".//DATATAKE_SENSING_START")[0].text)
        self.date = self.datetime.date()
        self.time = self.datetime.time()
        self.gml_coordinates = root.findall(".//EXT_POS_LIST")[0].text
  
        self.cloud_cover = "{:.3f}".format(float(root.findall(".//Cloud_Coverage_Assessment")[0].text))
        self.processing_level = root.findall(".//PROCESSING_LEVEL")[0].text
        self.tile_id = self.name[39:44]
        logging.info("  - Done!")

    def _parseTileMetadata(self, root):
        """Parsing general S2 tile metadata from eTree.Element type object.

        Args:
            root (eTree.Element): S2 tile metadata from eTree.Element type object
        """

        logging.info("  - Parsing Tile Metadata file...")
        epsg = root[1][0][1].text
        self.crs = pyproj.crs.CRS(epsg)
        logging.info("  - Done!")

    @staticmethod
    def setResolution(band):
        """ Getting band resolution for Sentinel 2.
        Args:
            band (str): Band short name as string
        Returns:
            str: Band resolution
        """
        resolutions = {
            "B01": "60",
            "B02": "10",
            "B03": "10",
            "B04": "10",
            "B05": "20",
            "B06": "20",
            "B07": "20",
            "B08": "10",
            "B8A": "20",
            "B09": "60",
            "B10": "60",
            "B11": "20",
            "B12": "20",
        }
        return resolutions.get(band)

    def getBands(self):
        """Finds all the available bands of an image and sets new attributes for each band.
        """

        bands = ['B02', 'B03', 'B04', 'B08', 'B05', 'B06', 'B07', 'B8A', 'B11', 'B12']

        for band in bands:
            resolution = self.setResolution(band)

            for (dirpath, dirnames, filenames) in os.walk(os.path.join(self.path, self.name)):
                for file in filenames:
                    if self.processing_level == 'Level-2A':
                        if fnmatch.fnmatch(file, "*{}*{}m*.jp2".format(band, resolution)):
                            setattr(self, 'datapath_{}'.format(resolution), os.path.join(dirpath))
                            break
                    else:
                        if fnmatch.fnmatch(file, "*_{}_*.jp2".format(band)):
                            logging.debug(os.path.join(dirpath, file))
                            setattr(self, 'datapath', os.path.join(dirpath))
                            break

            for (dirpath, dirnames, filenames) in os.walk(os.path.join(self.path, self.name)):
                for file in filenames:
                    if self.processing_level == 'Level-2A':
                        if fnmatch.fnmatch(file, "*{}*{}m*.jp2".format(band, resolution)):
                            logging.debug(os.path.join(dirpath, file))
                            setattr(self, '{}'.format(band), os.path.join(dirpath, file))
                    else:    
                        if fnmatch.fnmatch(file, "*_{}_*.jp2".format(band)):
                            logging.debug(os.path.join(dirpath, file))
                            setattr(self, '{}'.format(band), os.path.join(dirpath, file))
    @property
    def show_metadata(self):
        """Prints metadata using __dict__
        """
        print (self.__dict__)

class sentinel3():

    def __init__(self, path, name):
        """ A Sentinel 3 SLTRS image.
        Args:
            path (str, path-like): Path to image
            name (str): Name of the file
        """
        self.path = path
        self.name = name
        self.md_file = None
        self.satellite = None
        self.datetime = None
        self.date = None
        self.time = None
        self.str_datetime = None
        self.gml_coordinates = None
        self.cloud_cover = None
        self.processing_level = None
        self.number = None
        self.type = None
        self.crs = None
    
    def getmetadata(self):
        """Searching for metadata (XML) files.
        """
        for (dirpath, dirnames, filenames) in os.walk(os.path.join(self.path, self.name)):
            for file in filenames:
                if file.startswith("xfdumanifest"):
                    self.md_file = file
                    self._parseXML(dirpath, file)

    def _parseXML(self, path, file):
        """Parsing XML metadata file.
        Args:
            path (str, path-like): Path to file
            file (str): Name of the file
        """
        logging.info("  - Reading {}".format(os.path.join(self.path, self.name, file)))
        tree = lEtree.parse(os.path.join(self.path, self.name, file))
        root = tree.getroot()
        self.satellite = root.find(".//{*}familyName").text
        self.number = root.find(".//{*}number").text
        self.str_datetime = root.find(".//{*}startTime").text
        self.datetime = convert(self.str_datetime)
        self.date = self.datetime.date()
        self.time = self.datetime.time()
        self.gml_coordinates = root.find(".//{*}posList").text
        self.cloud_cover = "{:.3f}".format(float(root.find(".//{*}cloudyPixels").get("percentage")))
        self.processing_level = root[1][3][0][0][0][1].text.split("_")[1]
        self.type = root.find(".//{*}productType").text
        # Getting CRS Metadata
        footprint_metadata = root.find(".//{*}footPrint").get("srsName")
        response = urllib.request.urlopen(footprint_metadata).read()
        crs_root = lEtree.fromstring(response)
        crs = crs_root.find(".//{*}name").text
        self.crs = pyproj.crs.CRS(crs)
        logging.info("  - Done!")

    @property
    def show_metadata(self):
        """Prints metadata using __dict__
        """
        print (self.__dict__)