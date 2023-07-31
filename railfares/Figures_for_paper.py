import geopandas as gpd
import railfares.data_parsing as data_parsing
import matplotlib.pyplot as plt
import contextily as cx
import branca.colormap as cm
import pandas as pd
from matplotlib.colors import rgb2hex
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable



data_dir = '/Users/fb394/Documents/GitHub/railfares/railfares'

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 4326)
station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
# gb_boundary = gpd.read_file('http://geoportal1-ons.opendata.arcgis.com/datasets/f2c2211ff185418484566b2b7a5e1300_0.zip?outSR={%22latestWkid%22:27700,%22wkid%22:27700}')
gb_boundary = gpd.read_file('https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Countries_Dec_2021_GB_BFC_2022/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json')
gb_boundary = gb_boundary.to_crs(epsg = 4326)


stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
stations.to_crs(epsg = 27700, inplace = True)

############
# FIGURE 1
############


fig, ax = plt.subplots(figsize = (10,15))


stations.plot(ax = ax, color = '#F00000', linewidth = 0.1, edgecolor = '#000000', markersize = 40, alpha = 0.85)
cx.add_basemap(ax,
               crs = stations.crs,
               zoom = 7,
               source = cx.providers.MapBox(id = 'mapbox/dark-v10',
                                                    url = 'https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}',
                                                    accessToken = 'sk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsa2pyOG44YzByNTMzbHJlNnJ4NWkzd20ifQ.WirCqo3vfVc1pheemiAa0w',
                                                    attribution = '(C) Mapbox (C) OpenStreetMap contributors'))
ax.set_axis_off()


plt.savefig('/Users/fb394/Documents/GitHub/railfares/Figures/stations_location.pdf', dpi = 300)


############
# FIGURE 2
############

starting_station = 'EXETER ST DAVIDS'

od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv')

station_od = od_list[od_list['Origin station name'] == starting_station].copy()

station_od['Destination station name'] = station_od['Destination station name'].str.rstrip()

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 4326)
station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}))



station_od_gdf = stations.merge(station_od, left_on = 'CRS Code', right_on = 'destination_crs')

od_list_min = station_od_gdf.loc[station_od_gdf.groupby(['Destination station name'])['fare'].idxmin()]

od_list_min.to_crs(epsg = 27700, inplace = True)

colors = [(0, rgb2hex([255/255, 255/255, 255/255])), (1, rgb2hex([240/255, 0/255, 0/255]))]
custom_cmap = LinearSegmentedColormap.from_list('custom_colormap', colors)



fig, ax = plt.subplots(figsize = (10,15))

vmin = od_list_min['fare'].min()
vmax = od_list_min['fare'].max()

norm = Normalize(vmin=vmin, vmax=vmax)
sm = ScalarMappable(cmap=custom_cmap, norm=norm)
sm.set_array([])


od_list_min.plot(ax = ax, column = 'fare', linewidth = 0.1, edgecolor = '#000000', markersize = 40, alpha = 0.85, cmap = custom_cmap, legend = False, vmin = vmin, vmax = vmax)
cx.add_basemap(ax,
                crs = od_list_min.crs,
                zoom = 7,
                source = cx.providers.MapBox(id = 'mapbox/dark-v10',
                                                    url = 'https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}',
                                                    accessToken = 'sk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsa2pyOG44YzByNTMzbHJlNnJ4NWkzd20ifQ.WirCqo3vfVc1pheemiAa0w',
                                                    attribution = '(C) Mapbox (C) OpenStreetMap contributors'))
ax.set_axis_off()



# dummy_cmap = ScalarMappable(cmap=custom_cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
# # dummy_cmap.set_array([])

cax = fig.add_axes([0.7, 0.7, 0.03, 0.15])  # Adjust the position and size as needed
cb = plt.colorbar(sm, cax=cax)

cb.outline.set_edgecolor('white')  # Sets the color of the color bar outline (edge)
cb.ax.yaxis.set_tick_params(color='white')  # Sets the color of the tick labels

# Set the color of the tick labels' text on the color bar to white
for t in cb.ax.yaxis.get_ticklabels():
    t.set_color('white')
    
cb.set_label('Fare (£)', color='white')


plt.savefig('/Users/fb394/Documents/GitHub/railfares/Figures/cost_exeter.pdf', dpi = 300)


############
# FIGURE 3
############



stations_gb_gdf = stations.sjoin(gb_boundary)
stations_england_gdf = stations_gb_gdf[stations_gb_gdf['CTRY21NM'] == 'England'].copy().drop('index_right', axis = 1).dropna(axis = 0, subset = ['CRS Code'])


hospital_metrics = pd.read_csv(project_dir + 'number_hospitals_25_pounds.csv').merge(stations_england_gdf[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')


data_to_map = stations_england_gdf.merge(hospital_metrics, left_on = 'CRS Code', right_on = 'origin_crs', how = 'right')

# data_to_map = data_to_map.to_crs(epsg = 4326)
data_to_map.to_crs(epsg = 27700, inplace = True)

fig, ax = plt.subplots(figsize = (10,15))

vmin = data_to_map['Count'].min()
vmax = data_to_map['Count'].max()

norm = Normalize(vmin=vmin, vmax=vmax)
sm = ScalarMappable(cmap=custom_cmap, norm=norm)
sm.set_array([])


data_to_map.plot(ax = ax, column = 'Count', linewidth = 0.1, edgecolor = '#000000', markersize = 40, alpha = 0.85, cmap = custom_cmap, legend = False, vmin = vmin, vmax = vmax)
cx.add_basemap(ax,
                crs = data_to_map.crs,
                zoom = 7,
                source = cx.providers.MapBox(id = 'mapbox/dark-v10',
                                                    url = 'https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}',
                                                    accessToken = 'sk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsa2pyOG44YzByNTMzbHJlNnJ4NWkzd20ifQ.WirCqo3vfVc1pheemiAa0w',
                                                    attribution = '(C) Mapbox (C) OpenStreetMap contributors'))
ax.set_axis_off()



# dummy_cmap = ScalarMappable(cmap=custom_cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
# # dummy_cmap.set_array([])

cax = fig.add_axes([0.8, 0.63, 0.03, 0.15])  # Adjust the position and size as needed
cb = plt.colorbar(sm, cax=cax)

cb.outline.set_edgecolor('white')  # Sets the color of the color bar outline (edge)
cb.ax.yaxis.set_tick_params(color='white')  # Sets the color of the tick labels

# Set the color of the tick labels' text on the color bar to white
for t in cb.ax.yaxis.get_ticklabels():
    t.set_color('white')
    
cb.set_label('Count', color='white')


plt.savefig('/Users/fb394/Documents/GitHub/railfares/Figures/hospital_count_25_pounds.pdf', dpi = 300)


############
# FIGURE 4
############



stats_metrics = pd.read_csv(project_dir + 'stations_stats_and_pop_25_pounds.csv')
stats_metrics['Mean distance'] = stats_metrics['Mean distance']/1000

data_to_map = stations_england_gdf.merge(stats_metrics, left_on = 'CRS Code', right_on = 'Station CRS', how = 'right')

# data_to_map = data_to_map.to_crs(epsg = 4326)
data_to_map.to_crs(epsg = 27700, inplace = True)

fig, ax = plt.subplots(figsize = (10,15))

vmin = data_to_map['Mean distance'].min()
vmax = data_to_map['Mean distance'].max()

norm = Normalize(vmin=vmin, vmax=vmax)
sm = ScalarMappable(cmap=custom_cmap, norm=norm)
sm.set_array([])


data_to_map.plot(ax = ax, column = 'Mean distance', linewidth = 0.1, edgecolor = '#000000', markersize = 40, alpha = 0.85, cmap = custom_cmap, legend = False, vmin = vmin, vmax = vmax)
cx.add_basemap(ax,
                crs = data_to_map.crs,
                zoom = 7,
                source = cx.providers.MapBox(id = 'mapbox/dark-v10',
                                                    url = 'https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}',
                                                    accessToken = 'sk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsa2pyOG44YzByNTMzbHJlNnJ4NWkzd20ifQ.WirCqo3vfVc1pheemiAa0w',
                                                    attribution = '(C) Mapbox (C) OpenStreetMap contributors'))
ax.set_axis_off()



# dummy_cmap = ScalarMappable(cmap=custom_cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
# # dummy_cmap.set_array([])

cax = fig.add_axes([0.8, 0.63, 0.03, 0.15])  # Adjust the position and size as needed
cb = plt.colorbar(sm, cax=cax)

cb.outline.set_edgecolor('white')  # Sets the color of the color bar outline (edge)
cb.ax.yaxis.set_tick_params(color='white')  # Sets the color of the tick labels

# Set the color of the tick labels' text on the color bar to white
for t in cb.ax.yaxis.get_ticklabels():
    t.set_color('white')
    
cb.set_label('Mean distance (km)', color='white')


plt.savefig('/Users/fb394/Documents/GitHub/railfares/Figures/mean_distance_25_pounds.pdf', dpi = 300)



############
# FIGURE 5
############

od_list = od_list[od_list['fare'] < 1000]

fig, ax = plt.subplots()

od_list['fare'].plot(kind = 'hist', bins = 50, ax = ax, density = True, label = 'Histogram', color = '#F0B4B4')
od_list['fare'].plot(kind = 'density', ax = ax, label = 'Density', bw_method = 0.1, color = '#7878F0', linewidth = 2)

plt.xlabel('Fare (£)')
plt.ylabel('Density')

ax.set_xlim(-10,350)

ax.xaxis.set_major_locator(plt.MaxNLocator(5))
ax.yaxis.set_major_locator(plt.MaxNLocator(3))

plt.legend()

plt.savefig('/Users/fb394/Documents/GitHub/railfares/Figures/histogram_all_stations.pdf', dpi = 300)



############
# FIGURE 6
############

od_list = od_list[od_list['fare'] < 1000]

exmouth = od_list[od_list['origin_crs'] == 'EXM']
birmingham = od_list[od_list['origin_crs'] == 'EXD']

fig, ax = plt.subplots()

exmouth['fare'].plot(kind = 'hist', bins = 50, alpha = 0.75, ax = ax, density = True, label = 'Exmouth', color = '#F0B4B4')
exmouth['fare'].plot(kind = 'density', ax = ax, alpha = 0.75, label = 'Exmouth', bw_method = 0.1, color = '#F07878', linewidth = 2, linestyle = 'dashed')
birmingham['fare'].plot(kind = 'hist', bins = 50, alpha = 0.75, ax = ax, density = True, label = 'Birmingham', color = '#B4B4F0')
birmingham['fare'].plot(kind = 'density', ax = ax, alpha = 0.75, label = 'Birmingham', bw_method = 0.1, color = '#7878F0', linewidth = 2)

plt.xlabel('Fare (£)')
plt.ylabel('Density')

ax.set_xlim(-10,350)

ax.xaxis.set_major_locator(plt.MaxNLocator(5))
ax.yaxis.set_major_locator(plt.MaxNLocator(3))

plt.legend()

plt.savefig('/Users/fb394/Documents/GitHub/railfares/Figures/histogram_exmouth_exeter.pdf', dpi = 300)


