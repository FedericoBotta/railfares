import railfares.data_parsing as data_parsing
import pandas as pd
import geopandas as gpd
from folium.plugins import MarkerCluster
from matplotlib.colors import rgb2hex
import folium



project_dir = ''

#specify the name of a starting station; for instance, Exetet St Davids.
starting_station = 'exeter st davids'

#specify the maximum budget to use for the isocost calculation
budget = 10

#calculate the isocost; this next line returns a pandas data frame with all the
#stations that can be reached from the starting station with the given budget.
#The returned data frame contains the names of all the stations, and the
#corresponding fare. It also contains more technical information on the route,
#station code names, etc.
isocost = data_parsing.get_isocost_stations(starting_station, budget, project_dir)

#you can then create a map of the stations that can be reached. The following
#outputs to file an interactive html map

#first, set the file path and name
file_path_name = ''

#then create and output the map
data_parsing.plot_isocost_stations(starting_station, isocost, file_path_name, project_dir)




#You can also use the pre-calculated OD matrix to retrieve the cost of reaching
#any station from the starting station
#NOTE: this section requires to have the OD matrix file

#read the OD file. This is a large file so will take some time to read
#and use a significant amount of memory
od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

#select the entries corresponding to journeys starting at the starting station
#NOTE: the starting station string is converted to upper as in the OD matrix
#this is how the station names typically appear. This is for the tutorial purpose
#only, as in general it is more accurate to work with CRS or TIPLOC codes which are
#unique and do not depend on abbreviation of station names.
station_od = od_list[od_list['Origin station name'] == starting_station.upper()].copy()

#the next section creates a map to plot the cost of reaching any station
#from the starting station defined above.

#in order to create a map with a good colour scheme, we set a maximum price
#of 300 GBP; however, in practice this is never exceeded for journeys considered
#here.
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
    
station_od['marker_colour'] = pd.cut(station_od['fare'], bins = bins,
                                    labels =labels)

station_od['Destination station name'] = station_od['Destination station name'].str.rstrip()
station_od['popupText'] = ['Starting station: ' + starting_station + ',<br> Destination station: ' + row['Destination station name'].lower() + ',<br> Fare: £' + str(row['fare']).ljust(4,'0') for idx, row in station_od.iterrows()]

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 4326)

station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)

stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}))

station_od_gdf = stations.merge(station_od, left_on = 'CRS Code', right_on = 'destination_crs')

od_list_min = station_od_gdf.loc[station_od_gdf.groupby(['Destination station name'])['fare'].idxmin()]





cost_map = folium.Map(location = [station_gdf.dissolve().centroid[0].coords[0][1],station_gdf.dissolve().centroid[0].coords[0][0]], 
                      tiles = "https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsNnZzZmx1bDA0aXozYnA5NHNxc2oxYm4ifQ.NH-kHQqlCLP3OVnx5ygJlQ",
                      attr='mapbox', zoom_start = 7)
# svg_style = '<style>svg {background-color: white;}</style>'

# colormap.get_root().header.add_child(folium.Element(svg_style))
# cost_map.add_child(colormap)

marker_cluster = MarkerCluster(name = "Train stations").add_to(cost_map)

od_list_min = od_list_min.to_crs(epsg = 4326)

for idx, row in od_list_min.iterrows():
    
    
    folium.CircleMarker([row["geometry"].y, row['geometry'].x],
                  icon=folium.Icon(color = '#000000', icon_color=row['marker_colour']),
                  fill = True, fill_color = row['marker_colour'], color = '#000000', fill_opacity = 0.75, radius = 8, weight = 1,
                  popup = row['popupText']).add_to(cost_map)


file_path_name = ''
cost_map.save(file_path_name)
