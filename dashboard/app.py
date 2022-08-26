from flask import Flask, render_template, request,jsonify
# import json
import railfares.data_parsing as data_parsing
import pandas as pd
import geopandas as gpd
from matplotlib.colors import rgb2hex


project_dir = '/Users/fb394/Documents/GitHub/railfares/'
od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)
naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 4326)
station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
app=Flask(__name__)
@app.route('/', methods = ['GET', 'POST'])
def root():
    
   station_gdf = data_parsing.get_station_location(project_dir)
    
   list_stations = station_gdf['Station name'].unique()
   
   return render_template('index.html', list_stations = list_stations)

@app.route('/GetStationsGDF', methods = ['GET','POST'])
def get_stations_gdf():
    print('hello from app.py')
    
    stations_gdf = data_parsing.get_naptan_data(project_dir)
    stations_gdf.to_crs(epsg = '4326', inplace = True)
    stations_gdf['col'] = '#ff7800'
    stations_gdf['col'].iloc[0:1000] = '#0000F0'
    # print(stations_gdf.crs)
    # if request.method == 'POST':
        
    return jsonify({'data': stations_gdf.to_json()})
    # return jsonify({'data': jts_df.to_json()})
    #return jsonify({'data': stations_gdf.geometry})

@app.route('/PlotCost', methods = ['GET', 'POST'])
def plot_cost():
    
    starting_station = request.form['starting_station']

    # od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

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
        
    station_od['marker_colour'] = pd.cut(station_od['fare'], bins = bins,
                                        labels =labels)

    station_od['Destination station name'] = station_od['Destination station name'].str.rstrip()
    station_od['popupText'] = ['Starting station: ' + starting_station + ',<br> Destination station: ' + row['Destination station name'] + ',<br> Fare: £' + str(row['fare']).ljust(4,'0') for idx, row in station_od.iterrows()]
    
    stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}))


    station_od_gdf = stations.merge(station_od, left_on = 'CRS Code', right_on = 'destination_crs')
    
    od_list_min = station_od_gdf.loc[station_od_gdf.groupby(['Destination station name'])['fare'].idxmin()]
    
    return jsonify({'data': od_list_min.to_json()})


if __name__ == '__main__':
   app.run(host="localhost", port = 8080, debug=True)






#jts.get_lsoa_boundaries()