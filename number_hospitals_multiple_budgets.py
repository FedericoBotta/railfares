### This script calculates the number of hospitals that can be reached with different
### budgets, as set in the list budget.

import pandas as pd
import geopandas as gpd
import railfares.data_parsing as data_parsing

budget = [10,25,50,75,100,125,150,175,200]

data = pd.read_excel('https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1039129/journey-time-statistics-2019-destination-datasets.ods',
                     engine = 'odf', sheet_name = 'Hospitals', skiprows = 1, header = 1)

points = gpd.points_from_xy(data['Easting'], data['Northing'], crs = 'OSGB36 / British National Grid')
 
hospitals_gdf = gpd.GeoDataFrame(data, geometry = points)
hospitals_gdf.to_crs(epsg = 27700, inplace = True)

naptan_gdf = data_parsing.get_naptan_data()
naptan_gdf = naptan_gdf.to_crs(epsg = 27700)

station_gdf = data_parsing.get_station_location(tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}))

gb_boundary = gpd.read_file('https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Countries_Dec_2021_GB_BFC_2022/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json')
gb_boundary = gb_boundary.to_crs(epsg = 4326)

stations_gb_gdf = stations.sjoin(gb_boundary)
stations_england_gdf = stations_gb_gdf[stations_gb_gdf['CTRY21NM'] == 'England'].copy().drop('index_right', axis = 1).dropna(axis = 0, subset = ['CRS Code'])

closest_station_to_hospital_gdf = gpd.sjoin_nearest(hospitals_gdf, stations_england_gdf, max_distance = 5000, distance_col = 'distance')[['SiteCode', 'SiteName', 'CommonName', 'TIPLOC', 'Station name', 'CRS Code', 'distance']]
closest_station_to_hospital_gdf.rename(columns = {'CommonName': 'HospitalStationName', 'CRS Code': 'HospitalStationCRS'}, inplace = True)


od_list = pd.read_csv('od_minimum_cost_matrix.csv', low_memory = False)

subset_od_list = od_list[od_list['destination_crs'].isin(closest_station_to_hospital_gdf['HospitalStationCRS'])].reset_index(drop = True)

hospital_fares = pd.DataFrame()

for b in budget:

    for idx, row in stations_england_gdf.iterrows():
        
        if subset_od_list['origin_crs'].str.contains(row['CRS Code']).any():
            
            temp = subset_od_list[subset_od_list['origin_crs'] == row['CRS Code']].merge(closest_station_to_hospital_gdf, left_on = 'destination_crs', right_on = 'HospitalStationCRS')
            hospital_fares = pd.concat([hospital_fares, temp[temp['fare'] < b]])
            print(row['Station name'])
        
        else:
            
            print('Not found')
            print(row['Station name'])
            print('---')
    
    hospital_fares.drop_duplicates(subset = ['origin_crs', 'HospitalStationCRS'], inplace = True)
    hospital_fares.reset_index(drop = True, inplace = True)
    
    reachable_hospitals = hospital_fares.groupby(['origin_crs'])['SiteName'].count().reset_index().rename({'SiteName': 'Count'}, axis = 1)
    
    missing_stations = subset_od_list[~subset_od_list['origin_crs'].isin(reachable_hospitals['origin_crs'])]['origin_crs'].unique().tolist()   
    
    for crs in missing_stations:
        
        reachable_hospitals = pd.concat([reachable_hospitals, pd.DataFrame([[crs, 0]], columns = ['origin_crs', 'Count'])])
    
    reachable_hospitals.reset_index(drop = True, inplace = True)
    
    for idx, row in reachable_hospitals.iterrows():
        
        if closest_station_to_hospital_gdf['HospitalStationCRS'].str.contains(row['origin_crs']).any():
            
            reachable_hospitals.at[idx, 'Count'] = reachable_hospitals.at[idx, 'Count'] + 1

    reachable_hospitals.to_csv('number_hospitals_' + str(b) + '_pounds.csv')

