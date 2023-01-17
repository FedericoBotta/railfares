from flask import Flask, render_template, request,jsonify
# import json
import railfares.data_parsing as data_parsing
import pandas as pd
import geopandas as gpd
from matplotlib.colors import rgb2hex
import math
from urllib.request import urlopen
import numpy as np
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
url = 'https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA_Dec_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V3_2022/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=false&returnIdsOnly=true&outSR=4326&f=json'

response = urlopen(url)
json_data = response.read().decode()

id_list = json.loads(json_data)['objectIds']

lsoa_gdf = gpd.GeoDataFrame()

while id_list:
    
    temp_id = id_list[0:250]
    
    temp_url = 'https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA_Dec_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V3_2022/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json&objectIds=' + ','.join(str(x) for x in temp_id)
    
    temp_gdf = gpd.read_file(temp_url)
    
    lsoa_gdf = gpd.GeoDataFrame(pd.concat([lsoa_gdf, temp_gdf]))
    
    id_list = [x for x in id_list if x not in temp_id]
    

app=Flask(__name__)
@app.route('/', methods = ['GET', 'POST'])
def root():
    
   station_gdf = data_parsing.get_station_location(project_dir)
    
   list_stations = station_gdf['Station name'].unique().tolist()
   # list_stations.reverse()
   
   return render_template('index.html', list_stations = list_stations)

@app.route('/station_metrics/', methods = ['GET', 'POST'])
def station_metrics():
    
   metrics = ['Number of stations', 'Max distance', 'Mean distance', 'Median distance', 'Metric', 'Population Metric', 'Reachable Population']
   
   budgets = [10,25,50,75,100,125,150,175,200]
   
   return render_template('station_metrics.html', metrics = metrics, budgets = budgets)

@app.route('/hospital_metrics/', methods = ['GET', 'POST'])
def hospital_metrics():
    
   metrics = ['Count']
   
   budgets = [10,25,50,75,100,125,150,175,200]
   
   return render_template('hospital_metrics.html', metrics = metrics, budgets = budgets)


@app.route('/employment_metrics/', methods = ['GET', 'POST'])
def employment_metrics():
    
   metrics = ['Count']
   
   budgets = [10,25,50,75,100,125,150,175,200]
   
   return render_template('employment_metrics.html', metrics = metrics, budgets = budgets)

@app.route('/cost_exclusion_index/', methods = ['GET', 'POST'])
def cost_exclusion_index():
   
   budgets = [10,25,50,75,100,125,150,175,200]
   
   return render_template('cost_exclusion_index.html', budgets = budgets)


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

@app.route('/PlotStatsMetrics', methods = ['GET', 'POST'])
def plot_stats_metrics():
    
    metric = request.form['metric_to_plot']
    
    stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
    
    la_file = gpd.read_file(project_dir + 'Local_Authority_Districts_(May_2021)_UK_BFE/LAD_MAY_2021_UK_BFE_V2.shp')
    la_file = la_file.to_crs(epsg = 4326)

    census_data = pd.read_excel(project_dir + 'census2021firstresultsenglandwales1.xlsx', sheet_name = 'P04', skiprows = 6,
                                names = ['Area code', 'Area name', 'Population density'])

    la_census = la_file.merge(census_data, left_on = 'LAD21CD', right_on = 'Area code')

    station_la_pop = naptan_gdf.sjoin(la_census, how = 'left')

    station_la_pop.dropna(subset = 'Population density', inplace = True)
    
    station_la_crs = station_la_pop.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'}).dropna().drop_duplicates('CRS Code')
    
    stats_metrics = pd.read_csv(project_dir + 'stations_stats_and_pop_'+ request.form['budget_to_plot'] +'_pounds.csv').merge(station_la_crs[['CRS Code', 'Population density']], left_on = 'Station CRS', right_on = 'CRS Code')
    stats_metrics['Mean distance'] = stats_metrics['Mean distance']/1000
    stats_metrics['Median distance'] = stats_metrics['Median distance']/1000
    stats_metrics['Max distance'] = stats_metrics['Max distance']/1000
    stats_metrics['Metric'] = stats_metrics['Number'] * stats_metrics['Median distance']/len(station_gdf['Station name'].unique())
    stats_metrics['Population Metric'] = stats_metrics['Median distance']/(stats_metrics['Population density'])*100
    stats_metrics['Reachable Population'] = stats_metrics['Reachable Population']/stats_metrics['Reachable Population'].max()*100
    # stats_metrics['Metric'] = stats_metrics['Median distance'] / stats_metrics['Number']*100
    stats_metrics['Number'] = stats_metrics['Number']/len(station_gdf['Station name'].unique())*100
    
    if metric == 'Number of stations':
        
        metric = 'Number'
        
    
    max_distance = round(stats_metrics[metric].max())
    if metric == 'Number' or metric == 'Metric' :
        
        step = 1
        # step = round(max_distance/100)
    
    elif metric == 'Population Metric':
        
        step = round(max_distance/100)
    
    else:
        
        step = 5
        # step = round(max_distance/100)
        
    bins = list(range(0, max_distance + step, step))
    n_bins = math.ceil(max_distance / step)


    labels = []
    colour_step = 240/n_bins

    r = 240
    g = 240
    b= 240

    for i in range(0, int(n_bins), 1):
        
        labels.append(rgb2hex([r/255, (g)/255, (b)/255]))
        g = g - colour_step
        b = b - colour_step
        
    stats_metrics['marker_colour'] = pd.cut(stats_metrics[metric], bins = bins,
                                        labels =labels)
    
    data_to_map = stations.merge(stats_metrics, left_on = 'CRS Code', right_on = 'Station CRS', how = 'right')
    
    data_to_map = data_to_map.to_crs(epsg = 4326)
    
    if metric == 'Number':
        
        metric_string = 'Number of stations'
        data_to_map['popupString'] = '%'
    
    elif metric == 'Metric' or metric == 'Population Metric' or metric == 'Reachable Population':
        
        metric_string = 'Index'
        data_to_map['popupString'] = ''
        
    else:
        
        metric_string = metric
        data_to_map['popupString'] = 'km'
    
    data_to_map['popupText'] = ['Starting station: ' + row['Station name'] + ',<br> ' + metric_string + ': ' + str(round(row[metric])) + row['popupString'] for idx, row in data_to_map.iterrows()]
    
    return jsonify({'data': data_to_map.to_json()})


@app.route('/PlotHospitalMetrics', methods = ['GET', 'POST'])
def plot_hospital_metrics():
    
    metric = request.form['metric_to_plot']
    
    stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
    stations.to_crs(epsg = 4326, inplace = True)
    
    stations_gb_gdf = stations.sjoin(gb_boundary)
    stations_england_gdf = stations_gb_gdf[stations_gb_gdf['CTRY21NM'] == 'England'].copy().drop('index_right', axis = 1).dropna(axis = 0, subset = ['CRS Code'])

    
    hospital_metrics = pd.read_csv(project_dir + 'number_hospitals_'+ request.form['budget_to_plot'] +'_pounds.csv').merge(stations_england_gdf[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')
    
    
    max_count = round(hospital_metrics[metric].max())
    
    step = 5
        
    bins = list(range(0, max_count + step, step))
    n_bins = math.ceil(max_count / step)


    labels = []
    colour_step = 240/n_bins

    r = 240
    g = 240
    b= 240

    for i in range(0, int(n_bins), 1):
        
        labels.append(rgb2hex([r/255, (g)/255, (b)/255]))
        g = g - colour_step
        b = b - colour_step
        
    hospital_metrics['marker_colour'] = pd.cut(hospital_metrics[metric], bins = bins,
                                        labels =labels)
    
    data_to_map = stations_england_gdf.merge(hospital_metrics, left_on = 'CRS Code', right_on = 'origin_crs', how = 'right')
    
    data_to_map = data_to_map.to_crs(epsg = 4326)
    
    metric_string = metric
    
    data_to_map['popupText'] = ['Starting station: ' + row['Station name'] + ',<br> ' + metric_string + ': ' + str(round(row[metric])) for idx, row in data_to_map.iterrows()]
    
    return jsonify({'data': data_to_map.to_json()})

@app.route('/PlotEmploymentMetrics', methods = ['GET', 'POST'])
def plot_employment_metrics():
    
    metric = request.form['metric_to_plot']
    
    stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
    stations.to_crs(epsg = 4326, inplace = True)
    
    employment_metrics = pd.read_csv(project_dir + 'number_large_employment_centres_'+ request.form['budget_to_plot'] +'_pounds.csv').merge(stations[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')
    
    
    max_count = round(employment_metrics[metric].max())
    
    step = 5
        
    bins = list(range(0, max_count + step, step))
    n_bins = math.ceil(max_count / step)


    labels = []
    colour_step = 240/n_bins

    r = 240
    g = 240
    b= 240

    for i in range(0, int(n_bins), 1):
        
        labels.append(rgb2hex([r/255, (g)/255, (b)/255]))
        g = g - colour_step
        b = b - colour_step
        
    employment_metrics['marker_colour'] = pd.cut(employment_metrics[metric], bins = bins,
                                        labels =labels)
    
    data_to_map = stations.merge(employment_metrics, left_on = 'CRS Code', right_on = 'origin_crs', how = 'right')
    
    data_to_map = data_to_map.to_crs(epsg = 4326)
    
    metric_string = metric
    
    data_to_map['popupText'] = ['Starting station: ' + row['Station name'] + ',<br> ' + metric_string + ': ' + str(round(row[metric])) for idx, row in data_to_map.iterrows()]
    
    return jsonify({'data': data_to_map.to_json()})

@app.route('/PlotCTRSE', methods = ['GET', 'POST'])
def plot_ctrse():
    
    # naptan_gdf = naptan_gdf.to_crs(epsg = 27700)
    
    budget = request.form['budget']

    station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
    station_gdf = station_gdf.to_crs(epsg = 4326)
    stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
    stations = stations.to_crs(epsg = 4326)


    reduced_od_list = od_list[od_list['origin_crs'].isin(stations['CRS Code'])]

    mean_fares = stations.merge(reduced_od_list[['origin_crs', 'fare']].groupby('origin_crs').mean().reset_index(), right_on = 'origin_crs', left_on = 'CRS Code')
    
    lsoa_gdf.to_crs(epsg = 27700, inplace = True)
    mean_fares.to_crs(epsg = 27700, inplace = True)

    lsoa_mean_fares = gpd.sjoin_nearest(lsoa_gdf, mean_fares, max_distance = 5000, distance_col = 'distance')



    imd_df = pd.read_excel('https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/833978/File_5_-_IoD2019_Scores.xlsx', sheet_name = 'IoD2019 Scores')

    stn_imd_gdf = lsoa_mean_fares.merge(imd_df, left_on = 'LSOA11CD', right_on = 'LSOA code (2011)')

    # stn_imd_gdf['mean_fare_dec'] = pd.qcut(stn_imd_gdf['fare'], 10, labels = False)
    # stn_imd_gdf['imd_dec'] = pd.qcut(stn_imd_gdf['Index of Multiple Deprivation (IMD) Score'], 10, labels = False)

   
    stn_imd_gdf['ranked_fare'] = stn_imd_gdf['fare'].rank()
    stn_imd_gdf['ranked_fare'] = stn_imd_gdf['ranked_fare']/stn_imd_gdf['ranked_fare'].max()
    stn_imd_gdf['transformed_fare'] = -23 * np.log(1-stn_imd_gdf['ranked_fare']*(1-np.exp(-100/23)))

    stn_imd_gdf['ranked_imd'] = stn_imd_gdf['Index of Multiple Deprivation (IMD) Score'].rank()
    stn_imd_gdf['ranked_imd'] = stn_imd_gdf['ranked_imd']/stn_imd_gdf['ranked_imd'].max()
    stn_imd_gdf['transformed_imd'] = -23 * np.log(1-stn_imd_gdf['ranked_imd']*(1-np.exp(-100/23)))
    
    town_centres_metrics = pd.read_csv(project_dir + 'number_town_centres_' + str(budget) + '_pounds.csv').merge(stations[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')
    
    
    town_centres_metrics['ranked_count'] = town_centres_metrics['Count'].rank(ascending = False)
    town_centres_metrics['ranked_count'] = town_centres_metrics['ranked_count']/town_centres_metrics['ranked_count'].max()
    town_centres_metrics['transformed_town_centres_count'] = -23 * np.log(1-town_centres_metrics['ranked_count']*(1-np.exp(-100/23)))
    
    stn_imd_gdf = stn_imd_gdf.merge(town_centres_metrics[['origin_crs', 'CRS Code', 'transformed_town_centres_count']])
    
    employment_centres_metrics = pd.read_csv(project_dir + 'number_large_employment_centres_' + str(budget) + '_pounds.csv').merge(stations[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')
    
    employment_centres_metrics['ranked_count'] = employment_centres_metrics['Count'].rank(ascending = False)
    employment_centres_metrics['ranked_count'] = employment_centres_metrics['ranked_count']/employment_centres_metrics['ranked_count'].max()
    employment_centres_metrics['transformed_employment_centres_count'] = -23 * np.log(1-employment_centres_metrics['ranked_count']*(1-np.exp(-100/23)))
    
    stn_imd_gdf = stn_imd_gdf.merge(employment_centres_metrics[['origin_crs', 'CRS Code', 'transformed_employment_centres_count']])
    
    hospital_metrics = pd.read_csv(project_dir + 'number_hospitals_' + str(budget) + '_pounds.csv').merge(stations[['CRS Code']], left_on = 'origin_crs', right_on = 'CRS Code')
    
    hospital_metrics['ranked_count'] = hospital_metrics['Count'].rank(ascending = False)
    hospital_metrics['ranked_count'] = hospital_metrics['ranked_count']/hospital_metrics['ranked_count'].max()
    hospital_metrics['transformed_hospitals_count'] = -23 * np.log(1-hospital_metrics['ranked_count']*(1-np.exp(-100/23)))
    
    stn_imd_gdf = stn_imd_gdf.merge(hospital_metrics[['origin_crs', 'CRS Code', 'transformed_hospitals_count']])
    
    
    stn_imd_gdf['ctrse'] = stn_imd_gdf['transformed_fare'] + stn_imd_gdf['transformed_imd'] + stn_imd_gdf['transformed_town_centres_count'] + stn_imd_gdf['transformed_employment_centres_count'] + stn_imd_gdf['transformed_hospitals_count']

    max_count = round(stn_imd_gdf['ctrse'].max())
    
    step = 10
        
    bins = list(range(0, max_count + step, step))
    n_bins = math.ceil(max_count / step)


    labels = []
    colour_step = 240/n_bins

    r = 240
    g = 240
    b= 240

    for i in range(0, int(n_bins), 1):
        
        labels.append(rgb2hex([r/255, (g)/255, (b)/255]))
        g = g - colour_step
        b = b - colour_step
        
    stn_imd_gdf['marker_colour'] = pd.cut(stn_imd_gdf['ctrse'], bins = bins,
                                        labels =labels)
    
    stn_imd_gdf = stn_imd_gdf.to_crs(epsg = 4326)
    
    
    stn_imd_gdf['popupText'] = ['LSOA 2011 code: ' + row['LSOA11CD'] + ',<br> ' + 'CTRSE: '+ str(round(row['ctrse'])) for idx, row in stn_imd_gdf.iterrows()]
    
    return jsonify({'data': stn_imd_gdf.to_json()})
    
    
    
    

if __name__ == '__main__':
   app.run(host="localhost", port = 8080, debug=True)






#jts.get_lsoa_boundaries()