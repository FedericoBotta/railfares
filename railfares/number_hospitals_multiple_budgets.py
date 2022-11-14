import pandas as pd
import geopandas as gpd
import railfares.data_parsing as data_parsing
import folium
from folium.plugins import MarkerCluster
from matplotlib.colors import rgb2hex
import branca.colormap as cm

# data = pd.read_csv('http://filestore.nationalarchives.gov.uk/datasets/records/hospital-records.txt', sep='\t', encoding = 'ISO-8859-1')
data = pd.read_excel('https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1039129/journey-time-statistics-2019-destination-datasets.ods',
                     engine = 'odf', sheet_name = 'Hospitals', skiprows = 1, header = 1)

points = gpd.points_from_xy(data['Easting'], data['Northing'], crs = 'OSGB36 / British National Grid')
 
hospitals_gdf = gpd.GeoDataFrame(data, geometry = points)
hospitals_gdf.to_crs(epsg = 27700, inplace = True)

#hospitals_buffer_gdf = hospitals_gdf.copy()
# hospitals_buffer_gdf['geometry'] = hospitals_buffer_gdf.geometry.buffer(5000)

project_dir = '/Users/fb394/Documents/GitHub/railfares/'

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 27700)

station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}))


# stations_within_buffer = stations.sjoin(hospitals_buffer_gdf, how = 'left')

# msoa_boundaries = gpd.read_file(project_dir + 'Middle_Layer_Super_Output_Areas_(December_2011)_Boundaries_Full_Clipped_(BFC)_EW_V3/Middle_Layer_Super_Output_Areas_(December_2011)_Boundaries_Full_Clipped_(BFC)_EW_V3.shp')

# msoa_station_gdf = stations.sjoin(msoa_boundaries, how = 'left').drop('index_right', axis = 1)

# msoa_hospitals_gdf = hospitals_buffer_gdf.sjoin(msoa_boundaries, how = 'left')

# msoa_stations_hospitals = msoa_station_gdf.merge(msoa_hospitals_gdf, on = 'MSOA11CD')


gb_boundary = gpd.read_file('http://geoportal1-ons.opendata.arcgis.com/datasets/f2c2211ff185418484566b2b7a5e1300_0.zip?outSR={%22latestWkid%22:27700,%22wkid%22:27700}')

stations_gb_gdf = stations.sjoin(gb_boundary)
stations_england_gdf = stations_gb_gdf[stations_gb_gdf['ctry17nm'] == 'England'].copy().drop('index_right', axis = 1).dropna(axis = 0, subset = ['CRS Code'])

closest_station_to_hospital_gdf = gpd.sjoin_nearest(hospitals_gdf, stations_england_gdf, max_distance = 5000, distance_col = 'distance')[['SiteCode', 'SiteName', 'CommonName', 'TIPLOC', 'Station name', 'CRS Code', 'distance']]
closest_station_to_hospital_gdf.rename(columns = {'CommonName': 'HospitalStationName', 'CRS Code': 'HospitalStationCRS'}, inplace = True)

# stations_to_closest_hospital_gdf = gpd.sjoin_nearest(stations_england_gdf, hospitals_gdf, distance_col = 'distance')
# stations_to_closest_hospital_gdf.rename(columns = {'CommonName': 'DepartingStation', 'CRS Code': 'DepartingCRS'}, inplace = True)

# all_stations_to_hospital_gdf = stations_to_closest_hospital_gdf.merge(closest_station_to_hospital_gdf, on = 'SiteCode')


od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

subset_od_list = od_list[od_list['destination_crs'].isin(closest_station_to_hospital_gdf['HospitalStationCRS'])].reset_index(drop = True)

hospital_fares = pd.DataFrame()

budget = [10,25,50,75,100,125,150,175,200]

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

    reachable_hospitals.to_csv(project_dir + 'number_hospitals_' + str(b) + '_pounds.csv')

