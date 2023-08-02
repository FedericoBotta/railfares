import pandas as pd
import geopandas as gpd
import railfares.data_parsing as data_parsing


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

stn_distances.to_csv(project_dir + 'stations_pairwise_distances.csv')
