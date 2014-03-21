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

def _read_data(data='data/map.json'):
    """Returns a list of JSON dictionaries, one for each feature of
    the polygons.

    """
    with open(data) as json_file:
        x = json.load(json_file)
        return x['features']


def _force_ring(coords):
    """Returns a nested list of coordinates, ensuring that the
    coordinates form a ring with the first and last coordinates the
    same.

    """
    x = coords[0]
    if x[0] != x[-1]:
        return [x + x[-1]]
    else: 
        return [x]


def _polygon(coords):
    """Converts a list of coordinates to json"""
    return json.dumps({"type": "Polygon", "coordinates": _force_ring(coords)})


def _params(coords, year):
    """Returns a parameter dictionary for a post request"""
    p = _polygon(coords)
    return {"begin":year-1, "end":year, "geom":p}


def _grab_loss(coords, year):
    """Returns the loss in hectares of the supplied coordinates and
    year from the UMD data set hosted on Earth Engine via GFW API.

    """
    url = 'http://gfw-apis.appspot.com/datasets/umd'
    res = requests.post(url, data=_params(coords, year))
    return res.json()['loss']


def _process_entry(entry):
    """Converts the supplied entry, a multipolygon in json, into a
    list of dictionaries with loss information associated with year
    and province identifying information.  Ready for quick conversion
    to Pandas data frame.

    """
    name_1 = entry['properties']['NAME_1']
    name_2 = entry['properties']['NAME_2']
    coord_set = entry['geometry']['coordinates']

    res = []
    for yr in range(2001,2013):
       x = [_grab_loss(coord, yr) for coord in coord_set]
       xx = {'prov':name_1, 'subprov':name_2, 'year':yr, 'loss':sum(x)}
       res.append(xx)

    return res


def _filter_admin(prov, subprov, data='data/map.json'):
    """Accepts a province and subprovince name (strings) and a data
    source in json format and returns the multipolygon associated with
    that administrative unit.

    """
    polys = _read_data(data)
    
    def _spec_filter(xx):
        x = xx['properties']
        return (x['NAME_1'] == prov) & (x['NAME_2'] == subprov)
    
    return filter(_spec_filter, polys)

