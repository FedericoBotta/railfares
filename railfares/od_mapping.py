import railfares.data_parsing as data_parsing
import folium
import pandas as pd
from folium.plugins import MarkerCluster

project_dir = '/Users/fb394/Documents/GitHub/railfares/'


od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv')

exeter_od = od_list[od_list['Origin station name'] == 'YORK'].copy()

exeter_od['marker_colour'] = pd.cut(exeter_od['fare'], bins = [0,25,50,100,150,200,300],
                                    labels = ['#F0F0F0', '#F0C8C8', '#F0A0A0', '#F07878', '#F05050', '#F02828'])

exeter_od['Destination station name'] = exeter_od['Destination station name'].str.rstrip()

station_gdf = data_parsing.get_station_location(project_dir)
station_gdf = station_gdf.to_crs(epsg = 4326)


exeter_gdf = station_gdf.merge(exeter_od, left_on = 'Station name', right_on = 'Destination station name')

cost_map = folium.Map(location = [station_gdf.dissolve().centroid[0].coords[0][1],station_gdf.dissolve().centroid[0].coords[0][0]], tiles = "Stamen Terrain", zoom_start = 5)

marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)


for idx, row in exeter_gdf.iterrows():
    
    
    folium.CircleMarker([row["geometry"].y, row['geometry'].x],
                  icon=folium.Icon(color = 'white', icon_color=row['marker_colour']),
                  fill = True, fill_color = row['marker_colour'], color = 'None', fill_opacity = 1,
                  popup="Station: " + str(row['Station name'] + '<br>' + 'Fare: ' + str(row['fare']))).add_to(cost_map)






folium.LayerControl().add_to(cost_map)
cost_map.save(project_dir + 'york_station_map.html')




