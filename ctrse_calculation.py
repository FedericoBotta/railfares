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





budget = 25
max_dist = 50000

stn_distances = pd.read_csv(project_dir + 'stations_pairwise_distances.csv')

reduced_stn_distances = stn_distances[stn_distances['Distance'] <= max_dist]

od_list_max_dist = od_list.merge(reduced_stn_distances, left_on = ['origin_crs', 'destination_crs'], right_on = ['First CRS', 'Second CRS'])

station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
stations = stations.to_crs(epsg = 4326)


reduced_od_list = od_list_max_dist[od_list_max_dist['origin_crs'].isin(stations['CRS Code'])]

mean_fares = stations.merge(reduced_od_list[['origin_crs', 'fare']].groupby('origin_crs').mean().reset_index(), right_on = 'origin_crs', left_on = 'CRS Code')

lsoa_gdf.to_crs(epsg = 27700, inplace = True)
mean_fares.to_crs(epsg = 27700, inplace = True)

lsoa_mean_fares = gpd.sjoin_nearest(lsoa_gdf, mean_fares, max_distance = 5000, distance_col = 'distance')



imd_df = pd.read_excel('https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/833978/File_5_-_IoD2019_Scores.xlsx', sheet_name = 'IoD2019 Scores')

stn_imd_gdf = lsoa_mean_fares.merge(imd_df, left_on = 'LSOA11CD', right_on = 'LSOA code (2011)')

stn_distances = pd.read_csv(project_dir + 'stations_pairwise_distances.csv')

# stn_imd_gdf['mean_fare_dec'] = pd.qcut(stn_imd_gdf['fare'], 10, labels = False)
# stn_imd_gdf['imd_dec'] = pd.qcut(stn_imd_gdf['Index of Multiple Deprivation (IMD) Score'], 10, labels = False)


stn_imd_gdf['ranked_fare'] = stn_imd_gdf['fare'].rank()
stn_imd_gdf['ranked_fare'] = stn_imd_gdf['ranked_fare']/stn_imd_gdf['ranked_fare'].max()
stn_imd_gdf['transformed_fare'] = -23 * np.log(1-stn_imd_gdf['ranked_fare']*(1-np.exp(-100/23)))

stn_imd_gdf['ranked_imd'] = stn_imd_gdf['Index of Multiple Deprivation (IMD) Score'].rank()
stn_imd_gdf['ranked_imd'] = stn_imd_gdf['ranked_imd']/stn_imd_gdf['ranked_imd'].max()
stn_imd_gdf['transformed_imd'] = -23 * np.log(1-stn_imd_gdf['ranked_imd']*(1-np.exp(-100/23)))

town_centres_metrics = pd.read_csv(project_dir + 'number_town_centres_' + str(budget) + '_pounds.csv').merge(stations[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')


town_centres_metrics['ranked_count'] = town_centres_metrics['Count'].rank(ascending = False)
town_centres_metrics['ranked_count'] = town_centres_metrics['ranked_count']/town_centres_metrics['ranked_count'].max()
town_centres_metrics['transformed_town_centres_count'] = -23 * np.log(1-town_centres_metrics['ranked_count']*(1-np.exp(-100/23)))

stn_imd_gdf = stn_imd_gdf.merge(town_centres_metrics[['origin_crs', 'CRS Code', 'transformed_town_centres_count']])

employment_centres_metrics = pd.read_csv(project_dir + 'number_large_employment_centres_' + str(budget) + '_pounds.csv').merge(stations[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')

employment_centres_metrics['ranked_count'] = employment_centres_metrics['Count'].rank(ascending = False)
employment_centres_metrics['ranked_count'] = employment_centres_metrics['ranked_count']/employment_centres_metrics['ranked_count'].max()
employment_centres_metrics['transformed_employment_centres_count'] = -23 * np.log(1-employment_centres_metrics['ranked_count']*(1-np.exp(-100/23)))

stn_imd_gdf = stn_imd_gdf.merge(employment_centres_metrics[['origin_crs', 'CRS Code', 'transformed_employment_centres_count']])

hospital_metrics = pd.read_csv(project_dir + 'number_hospitals_' + str(budget) + '_pounds.csv').merge(stations[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')

hospital_metrics['ranked_count'] = hospital_metrics['Count'].rank(ascending = False)
hospital_metrics['ranked_count'] = hospital_metrics['ranked_count']/hospital_metrics['ranked_count'].max()
hospital_metrics['transformed_hospitals_count'] = -23 * np.log(1-hospital_metrics['ranked_count']*(1-np.exp(-100/23)))

stn_imd_gdf = stn_imd_gdf.merge(hospital_metrics[['origin_crs', 'CRS Code', 'transformed_hospitals_count']])


# stn_imd_gdf['ctrse'] = stn_imd_gdf['transformed_fare'] + stn_imd_gdf['transformed_imd'] + stn_imd_gdf['transformed_town_centres_count'] + stn_imd_gdf['transformed_employment_centres_count'] + stn_imd_gdf['transformed_hospitals_count']
stn_imd_gdf['ctrse'] = stn_imd_gdf['transformed_fare'] + stn_imd_gdf['transformed_town_centres_count'] + stn_imd_gdf['transformed_employment_centres_count'] + stn_imd_gdf['transformed_hospitals_count']


stn_imd_gdf.plot(column = 'ctrse', legend = True)

















