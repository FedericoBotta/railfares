import pandas as pd
import geopandas as gpd
import railfares.data_parsing as data_parsing
import matplotlib.pyplot as plt
from scipy.stats import kendalltau as kendall
from urllib.request import urlopen
import json
import numpy as np

project_dir = '/Users/fb394/Documents/GitHub/railfares/'

#the next section is commented because the data has now been saved to file.
#Uncomment to recalculate.

od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 27700)


station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
stations = stations.to_crs(epsg = 4326)


# lsoa_gdf = gpd.read_file('https://opendata.arcgis.com/datasets/1f23484eafea45f98485ef816e4fee2d_0.geojson')


url = 'https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA_Dec_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V3_2022/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=false&returnIdsOnly=true&outSR=4326&f=json'

response = urlopen(url)
json_data = response.read().decode()

id_list = json.loads(json_data)['objectIds']

lsoa_gdf = gpd.GeoDataFrame()

while id_list:
    
    temp_id = id_list[0:250]
    
    temp_url = 'https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA_Dec_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V3_2022/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json&objectIds=' + ','.join(str(x) for x in temp_id)
    
    temp_gdf = gpd.read_file(temp_url)
    
    lsoa_gdf = gpd.GeoDataFrame(pd.concat([lsoa_gdf, temp_gdf]))
    
    id_list = [x for x in id_list if x not in temp_id]





# stations_lsoa_gdf = lsoa_gdf.sjoin(stations)
# stations_lsoa_gdf = stations_lsoa_gdf.to_crs(epsg = 27700)


reduced_od_list = od_list[od_list['origin_crs'].isin(stations['CRS Code'])]

mean_fares = stations.merge(reduced_od_list[['origin_crs', 'fare']].groupby('origin_crs').mean().reset_index(), right_on = 'origin_crs', left_on = 'CRS Code')

lsoa_mean_fares = gpd.sjoin_nearest(lsoa_gdf, mean_fares, max_distance = 1000, distance_col = 'distance')



imd_df = pd.read_excel('https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/833978/File_5_-_IoD2019_Scores.xlsx', sheet_name = 'IoD2019 Scores')

stn_imd_gdf = lsoa_mean_fares.merge(imd_df, left_on = 'LSOA11CD', right_on = 'LSOA code (2011)')

# stn_imd_gdf['mean_fare_dec'] = pd.qcut(stn_imd_gdf['fare'], 10, labels = False)
# stn_imd_gdf['imd_dec'] = pd.qcut(stn_imd_gdf['Index of Multiple Deprivation (IMD) Score'], 10, labels = False)

stn_imd_gdf['ranked_fare'] = stn_imd_gdf['fare'].rank()
stn_imd_gdf['ranked_fare'] = stn_imd_gdf['ranked_fare']/stn_imd_gdf['ranked_fare'].max()
stn_imd_gdf['transformed_fare'] = -23 * np.log(1-stn_imd_gdf['ranked_fare']*(1-np.exp(-100/23)))

stn_imd_gdf['ranked_imd'] = stn_imd_gdf['Index of Multiple Deprivation (IMD) Score'].rank()
stn_imd_gdf['ranked_imd'] = stn_imd_gdf['ranked_imd']/stn_imd_gdf['ranked_imd'].max()
stn_imd_gdf['transformed_imd'] = -23 * np.log(1-stn_imd_gdf['ranked_imd']*(1-np.exp(-100/23)))


stn_imd_gdf['ctrse'] = stn_imd_gdf['transformed_fare'] + stn_imd_gdf['transformed_imd']


stn_imd_gdf.plot(column = 'ctrse', legend = True)

















