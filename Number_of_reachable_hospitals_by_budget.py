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

budget = 20

for idx, row in stations_england_gdf.iterrows():
    
    if subset_od_list['origin_crs'].str.contains(row['CRS Code']).any():
        
        temp = subset_od_list[subset_od_list['origin_crs'] == row['CRS Code']].merge(closest_station_to_hospital_gdf, left_on = 'destination_crs', right_on = 'HospitalStationCRS')
        hospital_fares = pd.concat([hospital_fares, temp[temp['fare'] < budget]])
        print(row['Station name'])
    
    else:
        
        print('Not found')
        print(row['Station name'])
        print('---')

hospital_fares.drop_duplicates(subset = ['origin_crs', 'HospitalStationCRS'], inplace = True)
hospital_fares.reset_index(drop = True, inplace = True)

reachable_hospitals = hospital_fares.groupby(['origin_crs'])['SiteName'].count().reset_index().rename({'SiteName': 'Count'}, axis = 1)


for idx, row in reachable_hospitals.iterrows():
    
    if closest_station_to_hospital_gdf['HospitalStationCRS'].str.contains(row['origin_crs']).any():
        
        reachable_hospitals.at[idx, 'Count'] = reachable_hospitals.at[idx, 'Count'] + 1





hospital_reach_gdf = stations_england_gdf.merge(reachable_hospitals, left_on = 'CRS Code', right_on = 'origin_crs')


max_price = 58
step = 1
bins = list(range(0, max_price + step, step))
n_bins = max_price / step


labels = []
colour_step = 240/n_bins

r = 240
g = 240
b= 240

for i in range(0, int(n_bins), 1):
    
    labels.append(rgb2hex([r/255, (g)/255, (b)/255]))
    g = g - colour_step
    b = b - colour_step

colormap = cm.LinearColormap(colors= labels, vmin = 0, vmax = max_price,
                             caption='Number of stations')

hospital_reach_gdf['marker_colour'] = pd.cut(hospital_reach_gdf['Count'], bins = bins,
                                    labels =labels, include_lowest = True)


cost_map = folium.Map(location = [station_gdf.dissolve().centroid[0].coords[0][1],station_gdf.dissolve().centroid[0].coords[0][0]], 
                      tiles = "https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsNnZzZmx1bDA0aXozYnA5NHNxc2oxYm4ifQ.NH-kHQqlCLP3OVnx5ygJlQ",
                      attr='mapbox', zoom_start = 7)
# svg_style = '<style>svg {background-color: white;}</style>'

# colormap.get_root().header.add_child(folium.Element(svg_style))
cost_map.add_child(colormap)

marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)

hospital_reach_gdf = hospital_reach_gdf.to_crs(epsg = 4326)

for idx, row in hospital_reach_gdf.iterrows():
    
    
    folium.CircleMarker([row["geometry"].y, row['geometry'].x],
                  icon=folium.Icon(color = '#000000', icon_color=row['marker_colour']),
                  fill = True, fill_color = row['marker_colour'], color = '#000000', fill_opacity = 0.75, radius = 8, weight = 1,
                  popup="Station: " + str(row['Station name'] + '<br>' + 'Count: ' + str(row['Count']))).add_to(cost_map)







# folium.LayerControl().add_to(cost_map)
cost_map.save(project_dir + 'reachable_hospital.html')






