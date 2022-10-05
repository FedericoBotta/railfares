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


budget = 200

stn_numbers = pd.DataFrame()

# for stn in od_list['Origin station name'].unique():
for idx, row in stations.iterrows():
        
    if row['CRS Code'] in od_list['origin_crs'].unique():
        
        # df = od_list[od_list['origin_crs'] == row['CRS Code']]
        df = od_list.query('origin_crs==@row["CRS Code"]')
        
        temp = df[df['fare'] <= budget]
        
        if not temp.empty:
            
            temp_gdf = stations.merge(temp, left_on = 'CRS Code', right_on = 'destination_crs')
            
            temp_gdf['distance'] = temp_gdf.geometry.apply(lambda x: row['geometry'].distance(x))
            
            stn_numbers = pd.concat([stn_numbers, pd.DataFrame([[row['CRS Code'], len(temp['Destination station name'].unique()), temp_gdf['distance'].max(), temp_gdf['distance'].mean(), temp_gdf['distance'].median()]], columns = ['Station CRS', 'Number', 'Max distance', 'Mean distance', 'Median distance'])])
            
            print(row['CRS Code'])
        

stn_numbers.to_csv(project_dir + 'stations_stats_200_pounds.csv')

# stn_numbers['Mean distance'] = stn_numbers['Mean distance']/1000

# max_distance = round(stn_numbers['Mean distance'].max())
# step = 5
# bins = list(range(0, max_distance + step, step))
# n_bins = math.ceil(max_distance / step)


# labels = []
# colour_step = 240/n_bins

# r = 240
# g = 240
# b= 240

# for i in range(0, int(n_bins), 1):
    
#     labels.append(rgb2hex([r/255, (g)/255, (b)/255]))
#     g = g - colour_step
#     b = b - colour_step

# colormap = cm.LinearColormap(colors= labels, vmin = 0, vmax = max_distance,
#                              caption='Price (£)')

# stn_numbers['marker_colour'] = pd.cut(stn_numbers['Mean distance'], bins = bins,
#                                     labels =labels)

# data_to_map = stations.merge(stn_numbers, left_on = 'CRS Code', right_on = 'Station CRS', how = 'right')

# cost_map = folium.Map(location = [station_gdf.dissolve().centroid[0].coords[0][1],station_gdf.dissolve().centroid[0].coords[0][0]], 
#                       tiles = "https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsNnZzZmx1bDA0aXozYnA5NHNxc2oxYm4ifQ.NH-kHQqlCLP3OVnx5ygJlQ",
#                       attr='mapbox', zoom_start = 7)
# # svg_style = '<style>svg {background-color: white;}</style>'

# # colormap.get_root().header.add_child(folium.Element(svg_style))
# cost_map.add_child(colormap)

# marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)

# data_to_map = data_to_map.to_crs(epsg = 4326)

# for idx, row in data_to_map.iterrows():
    
    
#     folium.CircleMarker([row["geometry"].y, row['geometry'].x],
#                   icon=folium.Icon(color = '#000000', icon_color=row['marker_colour']),
#                   fill = True, fill_color = row['marker_colour'], color = '#000000', fill_opacity = 0.75, radius = 8, weight = 1,
#                   popup="Station: " + str(row['CommonName'] + '<br>' + 'Distance: ' + str(row['Mean distance']))).add_to(cost_map)







# # folium.LayerControl().add_to(cost_map)
# cost_map.save(project_dir + 'mean_distance.html')



