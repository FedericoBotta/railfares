import railfares.data_parsing as data_parsing
import pandas as pd


project_dir = '/Users/fb394/Documents/GitHub/railfares/'


# start = time.process_time()
# flow_record['col'].str.extract('(?P<test>.)(.)(.{4})(.{4})(.{5})(.{3})(.)(.)(.{8})(.{8})(.{3})(.)(.)(.)(.{7})')
# print(time.process_time()-start)







station_gdf = data_parsing.get_station_location(project_dir)
loc_records_df = data_parsing.get_location_records('location record', project_dir)[['nlc_code', 'crs_code']]
station_gdf = station_gdf.merge(loc_records_df, left_on = 'CRS Code', right_on = 'crs_code', how = 'left').drop('crs_code',1).drop_duplicates().reset_index(drop = True)


stations_nlc_dict = {}

for idx, row in station_gdf.iterrows():
    
    stations_codes = data_parsing.get_cluster_from_nlc(row['nlc_code'], project_dir)['cluster_id'].to_list()
    stations_codes.append(row['nlc_code'])
    stations_nlc_dict[row['Station name']] = stations_codes
    print(idx)






tickets = data_parsing.get_ticket_type_records(project_dir)
validity = data_parsing.get_ticket_validity(project_dir)
# val_code = validity[validity['out_days'] == '01']['validity_code'].to_list()
val_code = validity['validity_code'].to_list()
single_tickets = pd.DataFrame([x for idx, x in tickets.iterrows() if x['end_date'] == '31122999' and x['tkt_class'] == '2' and x['tkt_type'] == 'S' and x['validity_code'] in val_code and 'anytime' in x['description'].lower()])


flow_df, fares_df = data_parsing.get_flow_records('both', project_dir)


od_list = pd.DataFrame()
progr = 0
for key, value in stations_nlc_dict.items():
    
    station_flows_df = flow_df[(flow_df['origin_code'].isin(value)) & (flow_df['end_date'] == '31122999')]

    station_list = station_flows_df['flow_id'].to_list()
    station_fares_df = fares_df[fares_df['flow_id'].isin(station_list)]
    station_singles = station_fares_df[station_fares_df['ticket_code'].isin(single_tickets['ticket_code'].to_list())]
    station_singles['fare'] = station_singles['fare'].astype(int)/100
    
    #look if flows/routes exist in reverse direction
    inverse_station_flows_df = flow_df[(flow_df['destination_code'].isin(value)) & (flow_df['end_date'] == '31122999') & (flow_df['direction'] == 'R')]
    inverse_station_list = inverse_station_flows_df['flow_id'].to_list()
    inverse_station_fares_df = fares_df[fares_df['flow_id'].isin(inverse_station_list)]
    inverse_station_singles = inverse_station_fares_df[inverse_station_fares_df['ticket_code'].isin(single_tickets['ticket_code'].to_list())]
    inverse_station_singles['fare'] = inverse_station_singles['fare'].astype(int)/100
    
    
    destination_stations = data_parsing.get_isocost_from_list(station_flows_df, station_singles, project_dir)
    #look at cost of routes in reverse direction
    inverse_destination_stations = data_parsing.get_isocost_from_list(inverse_station_flows_df, inverse_station_singles, project_dir, inverse = True)
    
    
    od_list = pd.concat([od_list, pd.concat([destination_stations, inverse_destination_stations])])
    
    print(progr)
    progr = progr + 1




