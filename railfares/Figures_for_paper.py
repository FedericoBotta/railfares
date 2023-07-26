import geopandas as gpd
import railfares.data_parsing as data_parsing
import matplotlib.pyplot as plt
import contextily as cx
import branca.colormap as cm
import pandas as pd
from matplotlib.colors import rgb2hex
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable



project_dir = '/Users/fb394/Documents/GitHub/railfares/'

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 4326)
station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
# gb_boundary = gpd.read_file('http://geoportal1-ons.opendata.arcgis.com/datasets/f2c2211ff185418484566b2b7a5e1300_0.zip?outSR={%22latestWkid%22:27700,%22wkid%22:27700}')
gb_boundary = gpd.read_file('https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Countries_Dec_2021_GB_BFC_2022/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json')
gb_boundary = gb_boundary.to_crs(epsg = 4326)


stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
stations.to_crs(epsg = 4326, inplace = True)

############
# FIGURE 1
############


fig, ax = plt.subplots(figsize = (10,15))


stations.plot(ax = ax, color = '#F00000', linewidth = 0.1, edgecolor = '#000000', markersize = 10, alpha = 0.75)
cx.add_basemap(ax,
               crs = stations.crs,
               zoom = 6,
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

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 4326)
station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}))



station_od_gdf = stations.merge(station_od, left_on = 'CRS Code', right_on = 'destination_crs')

od_list_min = station_od_gdf.loc[station_od_gdf.groupby(['Destination station name'])['fare'].idxmin()]

colors = [(0, rgb2hex([255/255, 255/255, 255/255])), (1, rgb2hex([240/255, 0/255, 0/255]))]
custom_cmap = LinearSegmentedColormap.from_list('custom_colormap', colors)



fig, ax = plt.subplots(figsize = (10,15))

vmin = od_list_min['fare'].min()
vmax = od_list_min['fare'].max()

norm = Normalize(vmin=vmin, vmax=vmax)
sm = ScalarMappable(cmap=custom_cmap, norm=norm)
sm.set_array([])


od_list_min.plot(ax = ax, column = 'fare', linewidth = 0.1, edgecolor = '#000000', markersize = 10, alpha = 0.75, cmap = custom_cmap, legend = False, vmin = vmin, vmax = vmax)
cx.add_basemap(ax,
                crs = stations.crs,
                zoom = 6,
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
    
cb.set_label('Fare (£)', color='white')


plt.savefig('/Users/fb394/Documents/GitHub/railfares/Figures/cost_exeter.pdf', dpi = 300)




