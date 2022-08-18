import railfares.data_parsing as data_parsing
import folium
import pandas as pd
from folium.plugins import MarkerCluster
from matplotlib.colors import rgb2hex
import branca.colormap as cm

project_dir = '/Users/fb394/Documents/GitHub/railfares/'

starting_station = 'EXETER ST DAVIDS'

od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv')

exeter_od = od_list[od_list['Origin station name'] == starting_station].copy()

max_price = 300
step = 10
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
                             caption='Price (£) for anytime day single from ' + starting_station.lower())

exeter_od['marker_colour'] = pd.cut(exeter_od['fare'], bins = bins,
                                    labels =labels)

exeter_od['Destination station name'] = exeter_od['Destination station name'].str.rstrip()

station_gdf = data_parsing.get_station_location(project_dir)
station_gdf = station_gdf.to_crs(epsg = 4326)


exeter_gdf = station_gdf.merge(exeter_od, left_on = 'Station name', right_on = 'Destination station name')

# cost_map = folium.Map(location = [station_gdf.dissolve().centroid[0].coords[0][1],station_gdf.dissolve().centroid[0].coords[0][0]], tiles = "Stamen Terrain", zoom_start = 5)


cost_map = folium.Map(location = [station_gdf.dissolve().centroid[0].coords[0][1],station_gdf.dissolve().centroid[0].coords[0][0]], 
                      tiles = "https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsNnZzZmx1bDA0aXozYnA5NHNxc2oxYm4ifQ.NH-kHQqlCLP3OVnx5ygJlQ",
                      attr='mapbox', zoom_start = 5)


marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)


for idx, row in exeter_gdf.iterrows():
    
    
    folium.CircleMarker([row["geometry"].y, row['geometry'].x],
                  icon=folium.Icon(color = 'white', icon_color=row['marker_colour']),
                  fill = True, fill_color = row['marker_colour'], color = 'None', fill_opacity = 0.75, radius = 5,
                  popup="Station: " + str(row['Station name'] + '<br>' + 'Fare: ' + str(row['fare']))).add_to(cost_map)



cost_map.add_child(colormap)


folium.LayerControl().add_to(cost_map)
cost_map.save(project_dir + 'exeter_station_map.html')




