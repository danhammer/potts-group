import os
import urllib
import json
import itertools

import pandas as pd
from osgeo import ogr

# Go from JSON to a measurement of UMD deforestation by year.  If you
# have a shapefile, you will have to convert and simplify the
# polygons, preserving topology.  The Earth Engine API does not
# support long, long requests.  You can convert the shapefile using
# OGR within the data subdirectory:

# ogr2ogr -f GeoJSON map.json map.shp -simplify 0.001

# You can also upload your various formats (csv, shp, kml, etc.) to
# CartoDB and export to JSON.  Regardless of the path you choose,
# young Padawan, JSON is the destination.  Specifically,
# data/map.json.

def _read_data(data = 'data/map.json'):
    """Returns a list of JSON dictionaries, one for each feature of
    the polygons.

    """
    with open(data) as json_file:
        x = json.load(json_file)
        return x['features']

def _get_url(params = {}):
    """Returns the string URL given the supplied parameters to hit the
    GFW api for UMD calculations.

    """
    endpoint = 'http://gfw-apis.appspot.com/datasets/umd'
    return '%s?%s' % (endpoint, urllib.urlencode(params))


def _polygon(coords):
    return {"type": "Polygon", "coordinates": coords}

def _params(coords, year):
    p = _polygon(coords)
    return {"begin":year-1, "end":year, "geom":p}

def _grab_loss(coords, year, name_dict = {}):
    url = _get_url(_params(coords, year))
    res = urllib.urlopen(url)
    return res.read()

def _process_entry(json_entry):
    name_1 = json_entry['properties']['NAME_1']
    name_2 = json_entry['properties']['NAME_2']
    coord_set = json_entry['geometry']['coordinates']

    res = []
    for coord in coord_set:
       x = [_grab_loss(coord, yr) for yr in range(2001,2013)]
       res.append(x)

    return res
