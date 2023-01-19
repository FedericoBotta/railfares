import pandas as pd
import geopandas as gpd
import railfares.data_parsing as data_parsing
import folium
from folium.plugins import MarkerCluster
from matplotlib.colors import rgb2hex
import branca.colormap as cm
import math

project_dir = '/Users/fb394/Documents/GitHub/railfares/'

od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 27700)


station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')



stn_distances = pd.DataFrame()


for idx, row in stations.iterrows():
    
    temp = stations.copy()
    
    temp['distance_endpoint_crs'] = row['CRS Code']
    temp['distance'] = temp.geometry.apply(lambda x: row['geometry'].distance(x))
    
    stn_distances = pd.concat([stn_distances, temp[['CRS Code', 'distance_endpoint_crs', 'distance']]])

stn_distances.rename(columns = {'CRS Code': 'First CRS', 'distance_endpoint_crs': 'Second CRS', 'distance': 'Distance'}, inplace = True)






stn_numbers = pd.DataFrame()

# for stn in od_list['Origin station name'].unique():
for idx, row in stations.iterrows():
        
    if row['CRS Code'] in od_list['origin_crs'].unique():
        
        # df = od_list[od_list['origin_crs'] == row['CRS Code']]
        df = od_list.query('origin_crs==@row["CRS Code"]')
        
    
        
        temp_gdf = stations.merge(df, left_on = 'CRS Code', right_on = 'destination_crs')
        
        temp_gdf['distance'] = temp_gdf.geometry.apply(lambda x: row['geometry'].distance(x))
        
        stn_numbers = pd.concat([stn_numbers, pd.DataFrame([[row['CRS Code'], len(df['Destination station name'].unique()), temp_gdf['distance'].max(), temp_gdf['distance'].mean(), temp_gdf['distance'].median(), temp_gdf.sjoin(msoa_boundaries_pop, how = 'left').drop_duplicates(subset = ['MSOA Code'])['All Ages'].sum()]],
                                                           columns = ['Station CRS', 'Number', 'Max distance', 'Mean distance', 'Median distance', 'Reachable Population'])])
        
        print(row['CRS Code'])
    

stn_numbers.to_csv(project_dir + 'stations_stats_and_pop_' + '_pounds.csv')
