import railfares.data_parsing as data_parsing
import pandas as pd
import geopandas as gpd
import alphashape
import folium

project_dir = '/Users/fb394/Documents/GitHub/railfares/'

starting_station = 'exeter st davids'

isocost_lines = gpd.GeoDataFrame()

for b in range(5,25,5):
    
    
    test = data_parsing.get_isocost_stations(starting_station, b, project_dir)
    
    # data_parsing.plot_isocost_stations(data_parsing.get_station_code_from_name(starting_station, project_dir)['crs_code'][0], test, project_dir + 'new_test_isocost.html', project_dir)
    
    
    alpha_shape = alphashape.alphashape(test)
    alpha_shape['max_cost'] = str(b)
    isocost_lines = gpd.GeoDataFrame(pd.concat([isocost_lines, alpha_shape]), crs = alpha_shape.crs)




color_dict = {'5': '#ffe6e6', '10': '#ffb3b3', '15': '#ff8080', '20': '#ff4d4d'}


style1 = {'fillColor': '#228B22', 'color': '#228B22'}
style2 = {'fillColor': '#00FFFFFF', 'color': '#00FFFFFF'}


m = folium.Map([50.854457, 4.377184], zoom_start=5, tiles='cartodbpositron')
folium.GeoJson(isocost_lines.to_json(), style_function = lambda feature: {'color': color_dict[feature['properties']['max_cost']]}).add_to(m)
# folium.GeoJson(test).add_to(m)
folium.LatLngPopup().add_to(m)
m.save(project_dir + 'polygon.html')












# tickets = data_parsing.get_ticket_type_records(project_dir)

# validity = data_parsing.get_ticket_validity(project_dir)

# # val_code = validity[validity['out_days'] == '01']['validity_code'].to_list()

# val_code = validity['validity_code'].to_list()

# single_tickets = pd.DataFrame([x for idx, x in tickets.iterrows() if x['end_date'] == '31122999' and x['tkt_class'] == '2' and x['tkt_type'] == 'S' and x['validity_code'] in val_code and 'anytime' in x['description'].lower()])

# station_nlc = data_parsing.get_station_code_from_name(starting_station, project_dir)['nlc_code']

# flow_df = data_parsing.get_flow_records('flow', project_dir)



# stations_codes = data_parsing.get_cluster_from_nlc(station_nlc[0], project_dir)['cluster_id'].to_list()
# stations_codes.append(station_nlc[0])




# station_flows_df = flow_df[(flow_df['origin_code'].isin(stations_codes)) & (flow_df['end_date'] == '31122999')]


# # station_flows_df = flow_df[flow_df['origin_code'] == station_nlc[0]]

# fares_df = data_parsing.get_flow_records('fares', project_dir)

# station_list = station_flows_df['flow_id'].to_list()

# station_fares_df = fares_df[fares_df['flow_id'].isin(station_list)]

# station_tickets = tickets[tickets['ticket_code'].isin(station_fares_df['ticket_code'].to_list())]

# station_singles = station_fares_df[station_fares_df['ticket_code'].isin(single_tickets['ticket_code'].to_list())]

# station_singles['fare'] = station_singles['fare'].astype(int)/100





# dest_station_flows_df = flow_df[(flow_df['destination_code'].isin(stations_codes)) & (flow_df['end_date'] == '31122999') & (flow_df['direction'] == 'R')]



# # dest_station_flows_df = flow_df[(flow_df['destination_code'] == station_nlc[0]) & (flow_df['direction'] == 'R')]

# dest_station_list = dest_station_flows_df['flow_id'].to_list()

# dest_station_fares_df = fares_df[fares_df['flow_id'].isin(dest_station_list)]

# dest_station_tickets = tickets[tickets['ticket_code'].isin(dest_station_fares_df['ticket_code'].to_list())]

# dest_station_singles = dest_station_fares_df[dest_station_fares_df['ticket_code'].isin(single_tickets['ticket_code'].to_list())]

# dest_station_singles['fare'] = dest_station_singles['fare'].astype(int)/100









# budget = 15

# isocost = station_singles[station_singles['fare'].apply(lambda x: x <= budget)]

# temp_isocost_route = station_flows_df[(station_flows_df['flow_id'].isin(isocost['flow_id'].to_list())) & (station_flows_df['end_date'] == '31122999')]



# temp_isocost_route['bool'] = [data_parsing.get_nlc_from_cluster(x, project_dir).empty for x in temp_isocost_route['destination_code']]
# stations_route = temp_isocost_route[temp_isocost_route['bool'] == True]
# clusters_route = temp_isocost_route[temp_isocost_route['bool'] == False]
# unique_clusters = pd.Series(clusters_route['destination_code'].unique())

# disagr_clusters = clusters_route.merge(data_parsing.get_nlc_from_cluster(pd.Series(unique_clusters),project_dir)[['cluster_id', 'cluster_nlc']], left_on = 'destination_code', right_on = 'cluster_id')

# isocost_route = pd.concat([stations_route, disagr_clusters])


# isocost_route['cluster_nlc'].fillna(isocost_route['destination_code'], inplace = True)


# isocost_destinations = data_parsing.get_station_name_from_code(isocost_route['cluster_nlc'], project_dir)

# isocost_fare = isocost_route.merge(isocost[['flow_id','fare']], left_on = 'flow_id', right_on = 'flow_id', how = 'left')

# destination_stations = isocost_destinations.merge(isocost_fare, left_on = 'nlc_code', right_on = 'cluster_nlc')



# dest_isocost = dest_station_singles[dest_station_singles['fare'].apply(lambda x: x <= budget)]

# temp_isocost_route = dest_station_flows_df[(dest_station_flows_df['flow_id'].isin(dest_isocost['flow_id'].to_list())) & (dest_station_flows_df['end_date'] == '31122999')]



# temp_isocost_route['bool'] = [data_parsing.get_nlc_from_cluster(x, project_dir).empty for x in temp_isocost_route['origin_code']]
# stations_route = temp_isocost_route[temp_isocost_route['bool'] == True]
# clusters_route = temp_isocost_route[temp_isocost_route['bool'] == False]
# unique_clusters = pd.Series(clusters_route['origin_code'].unique())

# disagr_clusters = clusters_route.merge(data_parsing.get_nlc_from_cluster(pd.Series(unique_clusters),project_dir)[['cluster_id', 'cluster_nlc']], left_on = 'origin_code', right_on = 'cluster_id')

# dest_isocost_route = pd.concat([stations_route, disagr_clusters])


# dest_isocost_route['cluster_nlc'].fillna(dest_isocost_route['origin_code'], inplace = True)



# dest_isocost_destinations = data_parsing.get_station_name_from_code(dest_isocost_route['cluster_nlc'], project_dir)

# dest_isocost_fare = dest_isocost_route.merge(dest_isocost[['flow_id','fare']], left_on = 'flow_id', right_on = 'flow_id', how = 'left')

# destination_stations_1 = dest_isocost_destinations.merge(dest_isocost_fare, left_on = 'nlc_code', right_on = 'cluster_nlc')



# test = pd.concat([destination_stations, destination_stations_1])
# data_parsing.plot_isocost_stations(data_parsing.get_station_code_from_name(starting_station, project_dir)['crs_code'][0], gpd.GeoDataFrame(test), project_dir + 'new_test_isocost.html', project_dir)




# data_parsing.plot_isocost_stations(data_parsing.get_station_code_from_name(starting_station, project_dir)['crs_code'][0], destination_stations, project_dir + 'isocost.html', project_dir)

