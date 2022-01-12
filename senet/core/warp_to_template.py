import tempfile
import os
import core.gdal_utils as gu
import core.snappy_utils as su

def warp(source:str, template:str, output:str, resample_algorithm:str = "cubicspline"):
    """Reprojects, resamples and subsets a source image to a template image using GDAL Warp.

    Args:
        source (str, pathlike): Path to source image 
        template (str): Path to template image
        output (str): Path to source image after the reprojection, resampling and subsetting
        resample_algorithm (str): Resampling method. Defaults to "cubicspline". See below for more options.\n
            +------------+-------------------+
            |Name        |Method             |
            +============+===================+
            |near        |Nearest Neighbor   |
            +------------+-------------------+
            |bilinear    |Bilinear           |
            +------------+-------------------+
            |cubic       |Cubic              |
            +------------+-------------------+
            |cubicspline |Cubic Spline       |
            +------------+-------------------+
            |lanczos     |Lanczos Windowed   |
            +------------+-------------------+
            |average     |Average            |
            +------------+-------------------+
            |mode        |Mode               |
            +------------+-------------------+
            |max         |Maximum            |
            +------------+-------------------+
            |min         |Minimum            |
            +------------+-------------------+
            |med         |Median             |
            +------------+-------------------+
            |q1          |First Quartile     |
            +------------+-------------------+
            |q3          |Third Quartile     |
            +------------+-------------------+
            For more information see `here <https://gdal.org/programs/gdalwarp.html> _`.\n
    """
    # Save source and template to GeoTIFF because it will need to be read by GDAL
    temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    temp_source_path = temp_file.name
    temp_file.close()
    su.copy_bands_to_file(source, temp_source_path)
    temp_file = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    temp_template_path = temp_file.name
    temp_file.close()
    su.copy_bands_to_file(template, temp_template_path)

    # Wrap the source based on tamplate
    wrapped = gu.resample_with_gdalwarp(temp_source_path, temp_template_path, resample_algorithm)

    # Save with snappy
    name, geo_coding = su.get_product_info(template)[0:2]
    bands = su.get_bands_info(source)
    for i, band in enumerate(bands):
        band['band_data'] = wrapped.GetRasterBand(i+1).ReadAsArray()
    su.write_snappy_product(output, bands, name, geo_coding)

    # Clean up
    try:
        os.remove(temp_source_path)
        os.remove(temp_template_path)
    except Exception:
        pass
