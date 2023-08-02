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

closest_station_to_large_employment_centres_gdf = gpd.sjoin_nearest(employment_centres_gdf, stations_england_gdf, max_distance = 5000, distance_col = 'distance')[['LSOACode', 'LSOAName', 'CommonName', 'TIPLOC', 'Station name', 'CRS Code', 'distance']]
closest_station_to_large_employment_centres_gdf.rename(columns = {'CommonName': 'large_employment_centresStationName', 'CRS Code': 'large_employment_centresStationCRS'}, inplace = True)

od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

subset_od_list = od_list[od_list['destination_crs'].isin(closest_station_to_large_employment_centres_gdf['large_employment_centresStationCRS'])].reset_index(drop = True)

large_employment_centres_fares = pd.DataFrame()

for idx, row in stations_england_gdf.iterrows():
    
    if subset_od_list['origin_crs'].str.contains(row['CRS Code']).any():
        
        temp = subset_od_list[subset_od_list['origin_crs'] == row['CRS Code']].merge(closest_station_to_large_employment_centres_gdf, left_on = 'destination_crs', right_on = 'large_employment_centresStationCRS')
        large_employment_centres_fares = pd.concat([large_employment_centres_fares, temp[temp['fare'] == temp['fare'].min()]])
        print(row['Station name'])
    
    else:
        
        print('Not found')
        print(row['Station name'])
        print('---')

large_employment_centres_fares.reset_index(drop = True, inplace = True)

for idx, row in large_employment_centres_fares.iterrows():
    
    if closest_station_to_large_employment_centres_gdf['large_employment_centresStationCRS'].str.contains(row['origin_crs']).any():
        
        large_employment_centres_fares.at[idx, 'fare'] = 0
        
        temp_large_employment_centres_df = closest_station_to_large_employment_centres_gdf[closest_station_to_large_employment_centres_gdf['large_employment_centresStationCRS'] == large_employment_centres_fares['origin_crs'].iloc[idx]]
        
        for col in temp_large_employment_centres_df.columns:
            
            large_employment_centres_fares.at[idx, col] = temp_large_employment_centres_df[col].iloc[0]


large_employment_centres_fares.to_csv(project_dir + 'large_employment_centres_fares.csv')


large_employment_centres_fares_gdf = stations_england_gdf.merge(large_employment_centres_fares, left_on = 'CRS Code', right_on = 'origin_crs')


max_price = 35
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
                             caption='Price (£)')

large_employment_centres_fares_gdf['marker_colour'] = pd.cut(large_employment_centres_fares_gdf['fare'], bins = bins,
                                    labels =labels)


cost_map = folium.Map(location = [station_gdf.dissolve().centroid[0].coords[0][1],station_gdf.dissolve().centroid[0].coords[0][0]], 
                      tiles = "https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsNnZzZmx1bDA0aXozYnA5NHNxc2oxYm4ifQ.NH-kHQqlCLP3OVnx5ygJlQ",
                      attr='mapbox', zoom_start = 7)

cost_map.add_child(colormap)

marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)

large_employment_centres_fares_gdf = large_employment_centres_fares_gdf.to_crs(epsg = 4326)

for idx, row in large_employment_centres_fares_gdf.iterrows():
    
    
    folium.CircleMarker([row["geometry"].y, row['geometry'].x],
                  icon=folium.Icon(color = '#000000', icon_color=row['marker_colour']),
                  fill = True, fill_color = row['marker_colour'], color = '#000000', fill_opacity = 0.75, radius = 8, weight = 1,
                  popup="Station: " + str(row['Station name_x'] + '<br>' + 'Fare: £' + str(row['fare'])) + '<br>' + 'Employment centre: ' +row['LSOAName']).add_to(cost_map)







# folium.LayerControl().add_to(cost_map)
cost_map.save(project_dir + 'large_employment_centres.html')






