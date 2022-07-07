import railfares.data_parsing as data_parsing
import pandas as pd

project_dir = '/Users/fb394/Documents/GitHub/railfares/'

starting_station = 'london paddington'

tickets = data_parsing.get_ticket_type_records(project_dir)

validity = data_parsing.get_ticket_validity(project_dir)

val_code = validity[validity['out_days'] == '01']['validity_code'].to_list()

single_tickets = pd.DataFrame([x for idx, x in tickets.iterrows() if x['end_date'] == '31122999' and x['tkt_class'] == '2' and x['tkt_type'] == 'S' and x['validity_code'] in val_code and 'anytime' in x['description'].lower()])

exeter_nlc = data_parsing.get_station_code_from_name(starting_station, project_dir)['nlc_code']

flow_df = data_parsing.get_flow_records('flow', project_dir)

exeter_flows_df = flow_df[flow_df['origin_code'] == exeter_nlc[0]]

fares_df = data_parsing.get_flow_records('fares', project_dir)

exeter_list = exeter_flows_df['flow_id'].to_list()

exeter_fares_df = fares_df[fares_df['flow_id'].apply(lambda x: x in exeter_list)]

exeter_tickets = tickets[tickets['ticket_code'].apply(lambda x: x in exeter_fares_df['ticket_code'].to_list())]

exeter_singles = exeter_fares_df[exeter_fares_df['ticket_code'].apply(lambda x: x in single_tickets['ticket_code'].to_list())]

exeter_singles['fare'] = exeter_singles['fare'].astype(int)/100



budget = 30

isocost = exeter_singles[exeter_singles['fare'].apply(lambda x: x <= budget)]

isocost_route = exeter_flows_df[(exeter_flows_df['flow_id'].apply(lambda x: x in isocost['flow_id'].to_list()) & exeter_flows_df['end_date'].apply(lambda x: x == '31122999'))]

isocost_destinations = data_parsing.get_station_name_from_code(isocost_route['destination_code'], project_dir)

isocost_fare = isocost_route.merge(isocost[['flow_id','fare']], left_on = 'flow_id', right_on = 'flow_id', how = 'left')

destination_stations = isocost_destinations.merge(isocost_fare, left_on = 'nlc_code', right_on = 'destination_code')

data_parsing.plot_isocost_stations(data_parsing.get_station_code_from_name(starting_station, project_dir)['crs_code'][0], destination_stations, project_dir + 'isocost.html', project_dir)

