import os
import urllib
import json
import itertools

import pandas as pd
import matplotlib.pyplot as plt

from osgeo import ogr


def _get_url(params = {}):
    """Returns the string URL given the supplied parameters to hit the
    GFW api for UMD calculations.

    """
    endpoint = 'http://gfw-apis.appspot.com/datasets/umd'
    return '%s?%s' % (endpoint, urllib.urlencode(params))


def _poly_loss(poly, year):
    """Returns the UMD forest cover loss for the polygon in the given
    year, relative to the previous year.
      
    Args:
      poly: gdal polygon instance
      year: integer value for the year, with 2001 <= year <= 2012

    """
    coords = poly.ExportToJson()
    params = {'geom': coords, 'begin': year - 1, 'end': year}
    url = _get_url(params)
    f = urllib.urlopen(url)
    return json.load(f)['loss']

def _get_loss(shp_path, year, prov, subprov):
    """Returns the year's forest cover loss for the supplied province
    and subprovince within the given shapefile path.

    Args:
      shp_path: string path relative to buffer directory
      year: integer value for the year, with 2001 <= year <= 2012
      prov: string province name (associated with GADM level 1)
      subprov: string subprovince name (associated with GADM level 2)
      
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shp_path, 0)
    layer = dataSource.GetLayer()
    layer.SetAttributeFilter("name_1 = '%s'" % prov)

    res = []
    # There may be multiple polygons for the given subprovince and GEE
    # only accepts calls for polygons, not multipolygons. Do one API
    # call each.
    for feature in layer:
        if feature.GetField("name_2") == subprov:
            geom = feature.GetGeometryRef()
            # geom is a multipolygon, 
            x = [_poly_loss(g, year) for g in geom]
            res.append(x)

    flattened = list(itertools.chain(*res))
    return {'prov':prov, 'subprov':subprov, 'year':year, 'loss':sum(flattened)}


def _plot_loss(prov='Jawa Timur', subprov='Gresik'):
    """Plots the line graph of UMD forest cover loss for the supplied
    Indonesian province and subprovince

    """
    idn = "data/idn_simple.shp"
    ts = [_get_loss(idn, yr, prov, subprov) for yr in range(2001, 2013)]
    df = pd.DataFrame(ts)
    plt.plot(df['year'], df['loss'])
    plt.show()
    return df
