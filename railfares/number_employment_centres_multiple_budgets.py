import pandas as pd
import geopandas as gpd
import railfares.data_parsing as data_parsing
import folium
from folium.plugins import MarkerCluster
from matplotlib.colors import rgb2hex
import branca.colormap as cm


data = pd.read_excel('https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1039129/journey-time-statistics-2019-destination-datasets.ods',
                     engine = 'odf', sheet_name = 'Large_employment_centres', skiprows = 1, header = 1)

points = gpd.points_from_xy(data['Easting'], data['Northing'], crs = 'OSGB36 / British National Grid')
 
employment_centres_gdf = gpd.GeoDataFrame(data, geometry = points)
employment_centres_gdf.to_crs(epsg = 27700, inplace = True)

project_dir = '/Users/fb394/Documents/GitHub/railfares/'

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 27700)

station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}))


gb_boundary = gpd.read_file('http://geoportal1-ons.opendata.arcgis.com/datasets/f2c2211ff185418484566b2b7a5e1300_0.zip?outSR={%22latestWkid%22:27700,%22wkid%22:27700}')

stations_gb_gdf = stations.sjoin(gb_boundary)
stations_england_gdf = stations_gb_gdf[stations_gb_gdf['ctry17nm'] == 'England'].copy().drop('index_right', axis = 1).dropna(axis = 0, subset = ['CRS Code'])

closest_station_to_employment_centre_gdf = gpd.sjoin_nearest(employment_centres_gdf, stations_england_gdf, max_distance = 5000, distance_col = 'distance')[['LSOACode', 'LSOAName', 'CommonName', 'TIPLOC', 'Station name', 'CRS Code', 'distance']]
closest_station_to_employment_centre_gdf.rename(columns = {'CommonName': 'EmploymentCentreStationName', 'CRS Code': 'EmploymentCentreStationCRS'}, inplace = True)


od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

subset_od_list = od_list[od_list['destination_crs'].isin(closest_station_to_employment_centre_gdf['EmploymentCentreStationCRS'])].reset_index(drop = True)

employment_centre_fares = pd.DataFrame()

budget = [150,175,200]

for b in budget:

    for idx, row in stations_england_gdf.iterrows():
        
        if subset_od_list['origin_crs'].str.contains(row['CRS Code']).any():
            
            temp = subset_od_list[subset_od_list['origin_crs'] == row['CRS Code']].merge(closest_station_to_employment_centre_gdf, left_on = 'destination_crs', right_on = 'EmploymentCentreStationCRS')
            employment_centre_fares = pd.concat([employment_centre_fares, temp[temp['fare'] < b]])
            print(row['Station name'])
        
        else:
            
            print('Not found')
            print(row['Station name'])
            print('---')
    
    employment_centre_fares.drop_duplicates(subset = ['origin_crs', 'EmploymentCentreStationCRS'], inplace = True)
    employment_centre_fares.reset_index(drop = True, inplace = True)
    
    reachable_employment_centres = employment_centre_fares.groupby(['origin_crs'])['LSOAName'].count().reset_index().rename({'LSOAName': 'Count'}, axis = 1)
    
    missing_stations = subset_od_list[~subset_od_list['origin_crs'].isin(reachable_employment_centres['origin_crs'])]['origin_crs'].unique().tolist()   
    
    for crs in missing_stations:
        
        reachable_employment_centres = pd.concat([reachable_employment_centres, pd.DataFrame([[crs, 0]], columns = ['origin_crs', 'Count'])])
    
    reachable_employment_centres.reset_index(drop = True, inplace = True)
    
    
    for idx, row in reachable_employment_centres.iterrows():
        
        if closest_station_to_employment_centre_gdf['EmploymentCentreStationCRS'].str.contains(row['origin_crs']).any():
            
            reachable_employment_centres.at[idx, 'Count'] = reachable_employment_centres.at[idx, 'Count'] + 1

    reachable_employment_centres.to_csv(project_dir + 'number_large_employment_centres_' + str(b) + '_pounds.csv')

