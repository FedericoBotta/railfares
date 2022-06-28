import data_parsing

tickets = data_parsing.get_ticket_type_records()

validity = data_parsing.get_ticket_validity()

val_code = validity[validity['out_days'] == '01']['validity_code'].to_list()

#single_tickets = tickets[(tickets['end_date'] == '31122999') & (tickets['tkt_class'] == '2') & (tickets['tkt_type'] == 'S') & (tickets['validity_code'] == val_code)]

single_tickets = pd.DataFrame([x for idx, x in tickets.iterrows() if x['end_date'] == '31122999' and x['tkt_class'] == '2' and x['tkt_type'] == 'S' and x['validity_code'] in val_code])

nlc_codes = data_parsing.get_nlc_codes()

exeter_nlc = nlc_codes[nlc_codes['Location'] == 'Exeter St Davids']['NLC'].to_list()

flow_df = data_parsing.get_flow_records('flow')

exeter_flows_df = flow_df[flow_df['origin_code'] == exeter_nlc[0][0:4]]

fares_df = data_parsing.get_flow_records('fares')

exeter_list = exeter_flows_df['flow_id'].to_list()

exeter_fares_df = fares_df[fares_df['flow_id'].apply(lambda x: x in exeter_list)]

exeter_tickets = tickets[tickets['ticket_code'].apply(lambda x: x in exeter_fares_df['ticket_code'].to_list())]

exeter_singles = exeter_fares_df[exeter_fares_df['ticket_code'].apply(lambda x: x in single_tickets['ticket_code'].to_list())]

exeter_singles['fare'] = exeter_singles['fare'].astype(int)/100


budget = 3

isocost = exeter_singles[exeter_singles['fare'].apply(lambda x: x < budget)]

isocost_route = exeter_flows_df[exeter_flows_df['flow_id'].apply(lambda x: x in isocost['flow_id'].to_list())]


