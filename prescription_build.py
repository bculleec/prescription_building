class Prescription:
    def __init__(self, total_acres = 0, average_rate = 0, total_product = 0, min_rate = 0, max_rate = 0):
        self.average_rate = average_rate
        self.total_product = total_product
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.total_acres = total_acres
        self.zones = []
    
    def print_table(self):
        print("---------------------------------------------------------")
        print(f"Average rate (lbs/ac) of fertilizer  | {self.average_rate}")
        print(f"Total product needed for script      |")
        print(f"(metric tonnes/ac)                   | {self.total_product}")
        print(f"Min rate                             | {self.min_rate}")
        print(f"Max rate                             | {self.max_rate}")
        print(f"Total acres                          | {self.total_acres}")
        print("---------------------------------------------------------")
        
    def set_average_rate(self, rate):
        self.average_rate = rate
    
    def set_total_product(self, amount):
        self.total_product = amount
    
    def set_min_rate(self, rate):
        self.min_rate = rate
    
    def set_max_rate(self, rate):
        self.max_rate = rate
    
    def auto_set_rates(self, zone_group):
        total_product = 0
        total_area = 0
        average_rate = 0
        min_rate = zone_group.zones[0].target_rate
        max_rate = zone_group.zones[0].target_rate

        for zone in zone_group.zones:
            total_product += zone.target_rate * zone.area
            total_area += zone.area
            if zone.target_rate < min_rate:
                min_rate = zone.target_rate
            if zone.target_rate > max_rate:
                max_rate = zone.target_rate
        
        average_rate = total_product / total_area
        self.total_acres = total_area
        self.total_product = total_product
        self.average_rate = average_rate
        self.min_rate = min_rate
        self.max_rate = max_rate

    def to_dataframe(self):
        data = [['Average rate (lbs/ac) of fertilizer ', self.average_rate],
                ['Total product needed for script (metric tonnes/ac)', self.total_product],
                ['Min Rate', self.min_rate],
                ['Max Rate', self.max_rate],
                ['Total acres', self.total_acres]]
        return pd.DataFrame(data, columns=['Description', 'Value'])

    def auto_update(self, changed_param, changed_ratio):
        if changed_param == "AVERAGE":
            print('User modified average value')

            # Update the total product value
            self.total_product = self.average_rate * self.total_acres
            self.min_rate = self.min_rate * changed_ratio
        
        return self


class Zone:
    def __init__(self, id, min_value = 0, max_value = 0, average_value = 0, area = 0, target_rate = 0):
        self.id = id
        self.area = area
        self.target_rate = target_rate
        self.min_value = min_value
        self.max_value = max_value
        self.average_value = average_value

class ZoneGroup:
    def __init__(self, zones):
        self.zones = zones
    
    def print_table(self):
        print('Zone ID | Min value in zone | Max value in zone | Average value in zone | Total Acres | Lbs/Ac Product in Script')
        for zone in self.zones:
            print(f"{zone.id} | {zone.min_value} | {zone.max_value} | {zone.average_value} | {zone.area} | {zone.target_rate}")

    def set_zone_rate(self, id, rate):
        for i in range (len(self.zones)):
            if (self.zones[i].id == id):
                self.zones[i].target_rate = rate
    
    def to_dataframe(self):
        data = []
        for zone in self.zones:
            data.append([zone.id, zone.min_value, zone.max_value, zone.average_value, zone.area, zone.target_rate])
        
        return pd.DataFrame(data, columns=['Zone ID', 'Min Value in zone', 'Max Value in zone', 'Average value in zone', 'Total Acres', 'Lbs/Ac Product in Script'])

import rasterio
from rasterio import features
from shapely.geometry import shape
import numpy as np
import pandas as pd
import math
import zipfile


import fiona
import pyproj
from shapely.ops import transform
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
import rasterio.features
import os

def export_shapefile(raster_path, zone_info):
    # print(zone_info)
    
    raster = rasterio.open(raster_path)

    print("Raster CRS:")
    print(raster.crs)

    # Reproject the raster to 4326
    # Reproject to 4326 first
    dstCrs = {'init': 'EPSG:4326'}
    srcCrs = raster.crs

    #calculate transform array and shape of reprojected raster
    transform, width, height = calculate_default_transform(
        raster.crs, dstCrs, raster.width, raster.height, *raster.bounds)

    kwargs = raster.meta.copy()
    kwargs.update({
            'crs': dstCrs,
            'transform': transform,
            'width': width,
            'height': height
        })
    #open destination raster
    dstRst = rasterio.open('./reprojected.tiff', 'w', **kwargs)
    #reproject and save raster band data
    for i in range(1, raster.count + 1):
        reproject(
            source=rasterio.band(raster, i),
            destination=rasterio.band(dstRst, i),
            #src_transform=raster.transform,
            src_crs=raster.crs,
            #dst_transform=transform,
            dst_crs=dstCrs,
            resampling=Resampling.nearest)
    #close destination raster
    dstRst.close()

    raster = rasterio.open('./reprojected.tiff')

    nodata = raster.meta['nodata']

    band1 = raster.read(1)

    mask = band1 != nodata

    i = 0

    filename = zone_info[1]['Filename']

    for zone in zone_info:
        i+=1
        # print(zone)

        # Grab the min and max value
        zone_min_value = zone['Min Val']
        zone_max_value = zone['Max Val']
        zone_target_rate = zone['Value']

        zone_mask = (band1 >= zone_min_value) & (band1 < zone_max_value)

        zone_poly = []

        for coords, value in features.shapes(zone_mask.astype(np.uint8), transform=raster.transform):
            # ignore polygons corresponding to nodata
            if value != 0:
                # convert geojson to shapely geometry
                geom = shape(coords)
                # print(geom)

                # Reproject geometry to 4326
                zone_poly.append(geom)

        schema = {
                'geometry': 'Polygon',
                'properties': {'Tgt_Rate': 'float'},
            }
        
        if os.path.exists(f"./{filename}.shp"):
            # Append to the existing shapefile
            mode = 'a'
        else:
            # Create a new shapefile
            mode = 'w'

        with fiona.open(f"./{filename}.shp", mode, 'ESRI Shapefile', schema,crs='epsg:4326',) as c:
            ## If there are multiple geometries, put the "for" loop here
            for geom in zone_poly:
                c.write({
                    'geometry': geom,
                    'properties': {'Tgt_Rate': zone_target_rate},
                })
    
    
    prefix = filename
    output_zip = 'prescription.zip'


    with zipfile.ZipFile(output_zip, 'w') as zipf:
        
        for filename in os.listdir('.'):
            
            if filename.startswith(prefix):
                zipf.write(filename)

    print(f'Zipped all files starting with "{prefix}" into "{output_zip}".')

    # Delete shp files
    for filename in os.listdir('.'):
        if filename.startswith(prefix):
            os.remove(filename)

    return output_zip


def read_zones(raster_path, num_zones):
    """Should return a list of zones given a raster path and the number of zones"""
    raster = rasterio.open(raster_path)
    
    # Reproject to 4326 first
    # dstCrs = {'init': 'EPSG:4326'}
    # srcCrs = raster.crs

    # #calculate transform array and shape of reprojected raster
    # transform, width, height = calculate_default_transform(
    #     raster.crs, dstCrs, raster.width, raster.height, *raster.bounds)

    # kwargs = raster.meta.copy()
    # kwargs.update({
    #         'crs': dstCrs,
    #         'transform': transform,
    #         'width': width,
    #         'height': height
    #     })
    # #open destination raster
    # dstRst = rasterio.open('./reprojected.tiff', 'w', **kwargs)
    # #reproject and save raster band data
    # for i in range(1, raster.count + 1):
    #     reproject(
    #         source=rasterio.band(raster, i),
    #         destination=rasterio.band(dstRst, i),
    #         #src_transform=raster.transform,
    #         src_crs=raster.crs,
    #         #dst_transform=transform,
    #         dst_crs=dstCrs,
    #         resampling=Resampling.nearest)
    # #close destination raster
    # dstRst.close()

    # raster = rasterio.open('./reprojected.tiff')

    nodata = raster.meta['nodata']

    num_zones = int(num_zones)

    print("NODATA IS : "+ str(nodata))
    
    band1 = raster.read(1)

    print("Band 1 values is : ",band1)

    mask = band1 != nodata


    stats = {
            'min': band1[mask].min(),
            'mean': band1[mask].mean(),
            'median': np.median(band1[mask]),
            'max': band1[mask].max()}

    print(raster.meta)
    print(stats)
    
    # Split band by equal quantiles
    band_range = stats['max'] - stats['min']
    print(band_range)
    print(num_zones)

    band_interval = band_range / num_zones

    # Use method from QGIS source code
    _values = np.sort(band1[mask])
    n = _values.size
    print(n)

    zones = []

    for i in range(num_zones):

        # Use percentile ranges instead

        # min_pct = i * math.floor(100 / num_zones)
        # max_pct = min_pct + math.floor(100 / num_zones)

        # zone_min_value = (i * band_interval) + stats['min']
        # zone_max_value = ((i+1) * band_interval) + stats['min']
        # zone_min_value = np.percentile(band1[mask], min_pct)
        # zone_max_value = np.percentile(band1[mask], max_pct)

        # Use method from QGIS source code
        q = (i) / (num_zones)
        qn = (i+1) / (num_zones)
        # print('q',q)
        a = q * (n - 1)
        an = qn * (n - 1)
        # print('a', a)
        aa = int(a)
        aan = int (an)
        # print('aa', aa)
        r = a - aa
        rn = an - aan
        # print('r',r)
        # print('values[aa]', _values[aa])
        Xq = ((1 - r) * _values[aa]) + (r * _values[aa + 1])
        
        if (i == num_zones - 1):
            Xqn = _values[_values.size-1]
        else:
            Xqn = ((1 - rn) * _values[aan]) + (rn * _values[aan + 1])

        print(i, Xq, Xqn)
        zone_min_value = Xq
        zone_max_value = Xqn

        zone_mask = (band1 >= zone_min_value) & (band1 < zone_max_value)

        # print('NUMBER OF FEATURES IN BAND ', band1[zone_mask].size)

        zone_avg_value = band1[zone_mask].mean()

        zone_poly = []
        zone_area_total = 0

        for coords, value in features.shapes(zone_mask.astype(np.uint8), transform = raster.transform):
            if (value != 0):
                geom = shape(coords)
                # if (geom.area < 18):
                #     print(geom)
                #     print(geom.area)
                
                # Use this code to reproject
                # project = pyproj.Transformer.from_proj(
                # pyproj.Proj(init='epsg:3857'), # source coordinate system
                # pyproj.Proj(init='epsg:3857')) # destination coordinate system

                # geom = transform(project.transform, geom)  # apply projection
                zone_poly.append(geom)
                zone_area_total += geom.area 

        # don't need to divide by 2
        zone_area_total*= 0.000247105 # * 0.5


        # schema = {
        #         'geometry': 'Polygon',
        #         'properties': {'id': 'int', 'area' : 'float'},
        #     }
        
        # with fiona.open(f"C:/Users/bculleechurn/Downloads/my_shp{i}.shp", 'w', 'ESRI Shapefile', schema) as c:
        #     ## If there are multiple geometries, put the "for" loop here
        #     for geom in zone_poly:
        #         c.write({
        #             'geometry': geom,
        #             'properties': {'id': 123, 'area' : zone_areas[geom]},
        #         })

        zones.append(Zone(id = i + 1, 
                          min_value=zone_min_value,
                          max_value=zone_max_value,
                          average_value = zone_avg_value,
                          area = zone_area_total
                          ))
    
    return ZoneGroup(zones=zones)

def prescription_from_zones(zone_group):
    zones = zone_group.zones
    total_area = 0

    for zone in zones:
        total_area += zone.area
    
    return Prescription(total_acres=total_area)

def zones_from_df(df):
    zones = []
    print('Starting zone processing from dataframe')

    for index, row in df.iterrows():
        zones.append(Zone(id = row['Zone ID'],
                          min_value=row['Min Value in zone'], 
                          max_value=row['Max Value in zone'],
                          average_value=row['Average value in zone'],
                          area = row['Total Acres'],
                          target_rate=row['Lbs/Ac Product in Script']))
    
    return ZoneGroup(zones)

def prescription_from_df(df):
    values = df['Value']

    return (Prescription(average_rate=values[0], total_product=values[1], min_rate=values[2], max_rate=values[3], total_acres=values[4]))

def main():
    p = Prescription()
    z = []

    r_path = "C:/Users/bculleechurn/Downloads/Ariss-Bicarb-P.tif"
    z = read_zones(r_path, 2)

    p = prescription_from_zones(z)

    z.print_table()

    p.print_table()

    z.set_zone_rate(id = 1, rate = 10)
    z.set_zone_rate(id = 2, rate = 20)
    z.print_table()

    p.auto_set_rates(zone_group=z)
    p.print_table()


