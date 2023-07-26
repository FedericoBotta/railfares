import pandas as pd
import geopandas as gpd
import railfares.data_parsing as data_parsing
import matplotlib.pyplot as plt
from scipy.stats import kendalltau as kendall
from urllib.request import urlopen
import json
import math
from matplotlib.colors import rgb2hex
import numpy as np
from flask import Flask, render_template, request,jsonify
# import json
import railfares.data_parsing as data_parsing
import railfares.functionalities as functionalities
import pandas as pd
import geopandas as gpd

import math
from urllib.request import urlopen
import numpy as np
import branca.colormap as cm
import folium
from folium.plugins import MarkerCluster
import json

project_dir = '/Users/fb394/Documents/GitHub/railfares/'
od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)
naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 4326)
station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
# gb_boundary = gpd.read_file('http://geoportal1-ons.opendata.arcgis.com/datasets/f2c2211ff185418484566b2b7a5e1300_0.zip?outSR={%22latestWkid%22:27700,%22wkid%22:27700}')
gb_boundary = gpd.read_file('https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Countries_Dec_2021_GB_BFC_2022/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json')
gb_boundary = gb_boundary.to_crs(epsg = 4326)

lsoa_gdf = functionalities.get_lsoa_boundaries()

stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
stations.to_crs(epsg = 4326, inplace = True)


od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

updated_od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix_april_2023_data.csv', low_memory = False)


old = od_list[['origin_crs', 'fare']].groupby(['origin_crs']).mean().reset_index().rename(columns = {'fare':'old_fare'})
new = updated_od_list[['origin_crs', 'fare']].groupby(['origin_crs']).mean().reset_index().rename(columns = {'fare':'new_fare'})

# diff = old.merge(new)

# diff['change'] = (diff['new_fare']-diff['old_fare'])/diff['old_fare']*100




# max_price = 4.0
# step = 0.25
# bins = list(np.arange(-2, max_price + step, step))
# n_bins = (max_price + 2) / step


# labels = []
# colour_step = 240/n_bins

# r = 240
# g = 240
# b= 240

# for i in range(0, int(n_bins), 1):
    
#     labels.append(rgb2hex([r/255, (g)/255, (b)/255]))
#     g = g - colour_step
#     b = b - colour_step

# colormap = cm.LinearColormap(colors= labels, vmin = 0, vmax = max_price,
#                              caption='Price (£)')

# stations_diff['marker_colour'] = pd.cut(stations_diff['change'], bins = bins,
#                                     labels =labels, include_lowest = True)


# cost_map = folium.Map(location = [stations_diff.dissolve().centroid[0].coords[0][1],stations_diff.dissolve().centroid[0].coords[0][0]], 
#                       tiles = "https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsNnZzZmx1bDA0aXozYnA5NHNxc2oxYm4ifQ.NH-kHQqlCLP3OVnx5ygJlQ",
#                       attr='mapbox', zoom_start = 7)

# cost_map.add_child(colormap)

# marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)

# stations_diff = stations_diff.to_crs(epsg = 4326)

# for idx, row in stations_diff.iterrows():
    
    
#     folium.CircleMarker([row["geometry"].y, row['geometry'].x],
#                   icon=folium.Icon(color = '#000000', icon_color=row['marker_colour']),
#                   fill = True, fill_color = row['marker_colour'], color = '#000000', fill_opacity = 0.75, radius = 8, weight = 1,
#                   popup="Station: " + "Change: " + str(round(row['change'],2))).add_to(cost_map)







# cost_map.save(project_dir + 'inflation_mean.html')






od_list['origin_crs'] = od_list['origin_crs'].apply(lambda x: x.strip())
updated_od_list['origin_crs'] = updated_od_list['origin_crs'].apply(lambda x: x.strip())
od_list['destination_crs'] = od_list['destination_crs'].apply(lambda x: x.strip())
updated_od_list['destination_crs'] = updated_od_list['destination_crs'].apply(lambda x: x.strip())

old = od_list[['origin_crs', 'destination_crs', 'fare']].reset_index().rename(columns = {'fare':'old_fare'})[['origin_crs', 'destination_crs', 'old_fare']]
new = updated_od_list[['origin_crs', 'destination_crs', 'fare']].reset_index().rename(columns = {'fare':'new_fare'})[['origin_crs', 'destination_crs', 'new_fare']]

change_list = []

for x in old['origin_crs'].unique():
    
    temp_old = old[old['origin_crs'] == x].groupby(['origin_crs', 'destination_crs'], as_index = False).min()
    temp_new = new[new['origin_crs'] == x].groupby(['origin_crs', 'destination_crs'], as_index = False).min()
    temp_list = temp_old.merge(temp_new, left_on = ['origin_crs','destination_crs'], right_on = ['origin_crs','destination_crs'])
    temp_list = temp_list[temp_list['origin_crs'].str.len() > 0]
    temp_list = temp_list[temp_list['destination_crs'].str.len() > 0]
    
    temp_list = temp_list.groupby(['origin_crs', 'destination_crs', 'old_fare'], as_index = False).min()
    
    temp_list['change'] = (temp_list['new_fare'] - temp_list['old_fare'])/temp_list['old_fare']*100
    
    change_list.append([x, temp_list['change'].mean()])
    
    print(x)

inflation_df = pd.DataFrame(change_list)

inflation_df.to_csv(project_dir + 'mean_price_change.csv')

inflation_gdf = stations.merge(inflation_df, left_on = 'CRS Code', right_on = '0')


max_price = 4.0
step = 0.25
bins = list(np.arange(-2.5, max_price + step, step))
n_bins = (max_price + 2.5) / step


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

inflation_gdf['marker_colour'] = pd.cut(inflation_gdf['1'], bins = bins,
                                    labels =labels, include_lowest = True)


cost_map = folium.Map(location = [inflation_gdf.dissolve().centroid[0].coords[0][1],inflation_gdf.dissolve().centroid[0].coords[0][0]], 
                      tiles = "https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsNnZzZmx1bDA0aXozYnA5NHNxc2oxYm4ifQ.NH-kHQqlCLP3OVnx5ygJlQ",
                      attr='mapbox', zoom_start = 7)

cost_map.add_child(colormap)

marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)

inflation_gdf = inflation_gdf.to_crs(epsg = 4326)

for idx, row in inflation_gdf.iterrows():
    
    
    folium.CircleMarker([row["geometry"].y, row['geometry'].x],
                  icon=folium.Icon(color = '#000000', icon_color=row['marker_colour']),
                  fill = True, fill_color = row['marker_colour'], color = '#000000', fill_opacity = 0.75, radius = 8, weight = 1,
                  popup="Station: " + "Change: " + str(round(row['1'],2))).add_to(cost_map)







cost_map.save(project_dir + 'inflation_mean_2022_2023.html')



