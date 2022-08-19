from flask import Flask, render_template, request,jsonify
# import json
import railfares.data_parsing as data_parsing
import pandas as pd
from matplotlib.colors import rgb2hex


project_dir = '/Users/fb394/Documents/GitHub/railfares/'
od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)
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
        
    exeter_od['marker_colour'] = pd.cut(exeter_od['fare'], bins = bins,
                                        labels =labels)

    exeter_od['Destination station name'] = exeter_od['Destination station name'].str.rstrip()
    exeter_od['popupText'] = ['Starting station: ' + starting_station + ',<br> Destination station: ' + row['Destination station name'] + ',<br> Fare: £' + str(row['fare']).ljust(5,'0') for idx, row in exeter_od.iterrows()]

    station_gdf = data_parsing.get_station_location(project_dir)
    station_gdf = station_gdf.to_crs(epsg = 4326)


    exeter_gdf = station_gdf.merge(exeter_od, left_on = 'CRS Code', right_on = 'destination_crs')
    
    return jsonify({'data': exeter_gdf.to_json()})


if __name__ == '__main__':
   app.run(host="localhost", port = 8080, debug=True)






#jts.get_lsoa_boundaries()