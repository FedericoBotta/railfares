### This script calculates an origin-destination (OD) style matrix for the cost
### of travelling between pairs of train stations in Great Britain.

import railfares.data_parsing as data_parsing
import pandas as pd
import json

project_dir = ''


with open(project_dir + 'all_station_nlc_codes.json', 'r') as fp:
    stations_nlc_dict = json.load(fp)

with open(project_dir + 'station_crs_dict.json', 'r') as fp:
    stations_crs_dict = json.load(fp)

flow_df, fares_df = data_parsing.get_flow_records('both')
tickets = data_parsing.get_ticket_type_records()
validity = data_parsing.get_ticket_validity()
val_code = validity['validity_code'].to_list()
single_tickets = pd.DataFrame([x for idx, x in tickets.iterrows() if x['end_date'] == '31122999' and x['tkt_class'] == '2' and x['tkt_type'] == 'S' and x['validity_code'] in val_code and 'anytime' in x['description'].lower()])
loc_records_df = data_parsing.get_location_records('location record')[['description', 'nlc_code', 'end_date']]
station_gdf = data_parsing.get_station_location()


clusters_dict = data_parsing.get_cluster_nlc_dict()

station_group_dict = data_parsing.fares_group_to_uic_dict()
group_to_station_dict = data_parsing.get_station_group_dictionary()
uic_to_names = data_parsing.uic_to_station_name_dict()
group_name_to_station_name_dict = data_parsing.station_group_to_stations_names_dict()

od_list = pd.DataFrame()
progr = 0

for key, value in stations_nlc_dict.items():
    
    # get the flows starting from the station and within valid date
    station_flows_df = flow_df[(flow_df['origin_code'].isin(value)) & (flow_df['end_date'] == '31122999')]

    # get list of flows from starting station
    station_list = station_flows_df['flow_id'].to_list()
    # get fares corresponding to the flows
    station_fares_df = fares_df[fares_df['flow_id'].isin(station_list)]
    # select fares corresponding to given ticket type
    station_singles = station_fares_df[station_fares_df['ticket_code'].isin(single_tickets['ticket_code'].to_list())].copy()
    #  convert fare to pounds
    station_singles['fare'] = station_singles['fare'].astype(int)/100
   
    # subset flows to only those corresponding to given ticket type
    temp_isocost_route = station_flows_df[(station_flows_df['flow_id'].isin(station_singles['flow_id'].to_list())) & (station_flows_df['end_date'] == '31122999')].copy()
    # create boolean column to check if destination station is in cluster or not
    temp_isocost_route['bool'] = [x in clusters_dict for x in temp_isocost_route['destination_code']]

    # separate stations from clusters
    stations_route = temp_isocost_route[temp_isocost_route['bool'] == False]
    clusters_route = temp_isocost_route[temp_isocost_route['bool'] == True]
    # get unique clusters
    unique_clusters = pd.Series(clusters_route['destination_code'].unique())
    # create data frame linking cluster ids to cluster nlc codes
    clust_nlc_df = pd.DataFrame([[k, clusters_dict.get(k)] for k in unique_clusters], columns = ['cluster_id', 'cluster_nlc']).explode('cluster_nlc')
    # split clusters into the various stations part of it
    disagr_clusters = clusters_route.merge(clust_nlc_df, left_on = 'destination_code', right_on = 'cluster_id').copy()
    # put together routes to stations and routes to disaggregated cluster
    isocost_route = pd.concat([stations_route, disagr_clusters])
    # fill nas that are due to the merge above (stations not from a cluster do not have a cluster nlc, so need filling)
    isocost_route['cluster_nlc'].fillna(isocost_route['destination_code'], inplace = True)
    

    # get nlc codes of destination stations
    station_code = isocost_route['cluster_nlc']
    
    if not isinstance(station_code, pd.Series):
        
        station_code = [station_code]
    
    # find destination stations in location records
    station_nlc = loc_records_df[(loc_records_df['nlc_code'].isin(station_code)) & (loc_records_df['end_date'] == '31122999')].drop_duplicates().drop('end_date', axis = 1).copy()
    # and merge with station geodataframe to find their name (currently not needed)
    # isocost_destinations = station_gdf.merge(station_nlc, left_on = 'CRS Code', right_on = 'crs_code', how = 'inner')
    # merge back with fares data to get destination stations names and fares
    isocost_fare = isocost_route.merge(station_singles[['flow_id','fare']], left_on = 'flow_id', right_on = 'flow_id', how = 'left').drop_duplicates().copy()
    
    destination_stations = station_nlc.merge(isocost_fare, left_on = 'nlc_code', right_on = 'cluster_nlc').copy()
    
    group_codes_indices = destination_stations.index[destination_stations['nlc_code'].isin(station_group_dict.keys())]
    group_codes_values = destination_stations[destination_stations['nlc_code'].isin(station_group_dict.keys())]
    
    destination_stations = destination_stations.astype({'description': object})
    
    if not group_codes_indices.empty:
        
        destination_stations['description'] = destination_stations.apply(lambda x: group_name_to_station_name_dict[x['description'].rstrip()] if x.name in group_codes_indices else x['description'], axis = 1)
        destination_stations = destination_stations.explode('description').explode('description')
    
    
    # repeat the same as above, but looking at existing reverse flows
    inverse_station_flows_df = flow_df[(flow_df['destination_code'].isin(value)) & (flow_df['end_date'] == '31122999') & (flow_df['direction'] == 'R')]
    inverse_station_list = inverse_station_flows_df['flow_id'].to_list()
    inverse_station_fares_df = fares_df[fares_df['flow_id'].isin(inverse_station_list)]
    inverse_station_singles = inverse_station_fares_df[inverse_station_fares_df['ticket_code'].isin(single_tickets['ticket_code'].to_list())].copy()
    inverse_station_singles['fare'] = inverse_station_singles['fare'].astype(int)/100
    
    
    
    temp_isocost_route = inverse_station_flows_df[(inverse_station_flows_df['flow_id'].isin(inverse_station_singles['flow_id'].to_list())) & (inverse_station_flows_df['end_date'] == '31122999')].copy()
    
    temp_isocost_route['bool'] = [x in clusters_dict  for x in temp_isocost_route['origin_code']]
    stations_route = temp_isocost_route[temp_isocost_route['bool'] == False]
    clusters_route = temp_isocost_route[temp_isocost_route['bool'] == True]
    unique_clusters = pd.Series(clusters_route['origin_code'].unique())
    
    clust_nlc_df = pd.DataFrame([[k, clusters_dict.get(k)] for k in unique_clusters], columns = ['cluster_id', 'cluster_nlc']).explode('cluster_nlc')

    disagr_clusters = clusters_route.merge(clust_nlc_df, left_on = 'origin_code', right_on = 'cluster_id')
    
    isocost_route = pd.concat([stations_route, disagr_clusters])
    isocost_route['cluster_nlc'].fillna(isocost_route['origin_code'], inplace = True)
    
    station_code = isocost_route['cluster_nlc']
    
    if not isinstance(station_code, pd.Series):
        
        station_code = [station_code]
    
    station_nlc = loc_records_df[(loc_records_df['nlc_code'].isin(station_code)) & (loc_records_df['end_date'] == '31122999')].drop_duplicates().drop('end_date', axis = 1).copy()
    
    isocost_fare = isocost_route.merge(inverse_station_singles[['flow_id','fare']], left_on = 'flow_id', right_on = 'flow_id', how = 'left').drop_duplicates().copy()
    
    
    
    
    
    inverse_destination_stations = station_nlc.merge(isocost_fare, left_on = 'nlc_code', right_on = 'cluster_nlc').copy()
    
    
    
    group_codes_indices = inverse_destination_stations.index[inverse_destination_stations['nlc_code'].isin(station_group_dict.keys())]
    group_codes_values = inverse_destination_stations[inverse_destination_stations['nlc_code'].isin(station_group_dict.keys())]
    
    inverse_destination_stations = inverse_destination_stations.astype({'description': object})
    
    if not group_codes_indices.empty:
        
        inverse_destination_stations['description'] = inverse_destination_stations.apply(lambda x: group_name_to_station_name_dict[x['description'].rstrip()] if x.name in group_codes_indices else x['description'], axis = 1)
        inverse_destination_stations = inverse_destination_stations.explode('description').explode('description')
    
    
    
    inverse_destination_stations.rename(columns = {'origin_code': 'temp origin_code', 'destination_code': 'temp destination_code'}, inplace = True)
    
    inverse_destination_stations.rename(columns = {'temp origin_code': 'destination_code', 'temp destination_code': 'origin_code'}, inplace = True)
    
    if not destination_stations.empty and not inverse_destination_stations.empty:

        od_df = pd.concat([destination_stations, inverse_destination_stations], ignore_index = True)[['description', 'nlc_code', 'origin_code','destination_code', 
                                                                                                     'route_code', 'end_date', 'start_date', 'toc',
                                                                                                     'flow_id', 'cluster_id', 'fare']].copy()
    elif inverse_destination_stations.empty:
        
        od_df = destination_stations[['description', 'nlc_code', 'origin_code','destination_code', 
                                                                                                     'route_code', 'end_date', 'start_date', 'toc',
                                                                                                     'flow_id', 'cluster_id', 'fare']].copy()
    
    elif destination_stations.empty:
        
        od_df = inverse_destination_stations[['description', 'nlc_code', 'origin_code','destination_code', 
                                                                                                     'route_code', 'end_date', 'start_date', 'toc',
                                                                                                     'flow_id', 'cluster_id', 'fare']].copy()
        
    # od_df.rename(columns = {'Station name': 'Destination station name'}, inplace = True)
    od_df.rename(columns = {'description': 'Destination station name'}, inplace = True)
    
    if not key in group_name_to_station_name_dict.keys():
        
        od_df['Origin station name'] = key
        
    else:
        
        od_df['Origin station name'] = ''
        od_df['Origin station name'] = od_df.apply(lambda x: group_name_to_station_name_dict[key], axis = 1)
        od_df = od_df.explode('Origin station name')
    
    od_df_min = od_df.loc[od_df.groupby('Destination station name')['fare'].idxmin()]
    
    od_df_min['origin_crs'] = [stations_crs_dict[row['Origin station name'].rstrip()] if row['Origin station name'] in stations_crs_dict.keys() else ' ' for idx, row in od_df_min.iterrows()]
    od_df_min['destination_crs'] = [stations_crs_dict[row['Destination station name'].rstrip()] if row['Destination station name'].rstrip() in stations_crs_dict.keys() else ' ' for idx, row in od_df_min.iterrows()]
    
    if any(x in value for x in od_df_min['destination_code']):
        
        raise Warning('Starting station is also in destination station')
        break
    
    od_list = pd.concat([od_list, od_df_min])
    
    print('Station: ' ,key, ', index ', progr)
    progr = progr + 1


od_list.to_csv(project_dir + 'od_minimum_cost_matrix.csv')


