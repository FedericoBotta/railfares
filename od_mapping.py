### This script plots a map with the cost of travelling to each station from the
### starting station specified at the start of this script.

import railfares.data_parsing as data_parsing
import folium
import pandas as pd
from folium.plugins import MarkerCluster
from matplotlib.colors import rgb2hex
import geopandas as gpd
import branca.colormap as cm

starting_station = 'NEWCASTLE'

od_list = pd.read_csv('od_minimum_cost_matrix.csv')

station_od = od_list[od_list['Origin station name'] == starting_station].copy()

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


station_od['marker_colour'] = pd.cut(station_od['fare'], bins = bins,
                                    labels =labels)

station_od['Destination station name'] = station_od['Destination station name'].str.rstrip()

naptan_gdf = data_parsing.get_naptan_data()
naptan_gdf = naptan_gdf.to_crs(epsg = 4326)
station_gdf = data_parsing.get_station_location(tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}))



station_od_gdf = stations.merge(station_od, left_on = 'CRS Code', right_on = 'destination_crs')

od_list_min = station_od_gdf.loc[station_od_gdf.groupby(['Destination station name'])['fare'].idxmin()]

cost_map = folium.Map(location = [station_gdf.dissolve().centroid[0].coords[0][1],station_gdf.dissolve().centroid[0].coords[0][0]], 
                      tiles = "Stamen Toner", zoom_start = 7)

cost_map.add_child(colormap)

marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)


for idx, row in od_list_min.iterrows():
    
    
    folium.CircleMarker([row["geometry"].y, row['geometry'].x],
                  icon=folium.Icon(color = '#000000', icon_color=row['marker_colour']),
                  fill = True, fill_color = row['marker_colour'], color = '#000000', fill_opacity = 0.75, radius = 8, weight = 1,
                  popup="Station: " + str(row['Station name'] + '<br>' + 'Fare: ' + str(row['fare']))).add_to(cost_map)






cost_map.save('newcastle_map.html')




