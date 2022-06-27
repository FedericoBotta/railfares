import pandas as pd
import csv
import re


project_dir = '/Users/fb394/Documents/GitHub/railfares/'


def get_station_clusters():
    
    
    with open(project_dir + 'RJFAF214/RJFAF214.FSC', newline = '') as f:
        reader = csv.reader(f)
        for row in reader:
    
            if "Records" in row[0]:
                number_rows = int(re.findall(r'\d+', row[0])[0])
                break
    
    station_clusters = pd.read_csv(project_dir + 'RJFAF214/RJFAF214.FSC', skiprows = 6, nrows = number_rows, names = ['col'])
    
    return pd.DataFrame({'update-marker': station_clusters['col'].str[0],
                   'cluster_id': station_clusters['col'].str[1:5],
                   'cluster_nlc': station_clusters['col'].str[5:9],
                   'end_date': station_clusters['col'].str[9:17],
                   'start_date': station_clusters['col'].str[17:25]})


def get_location_records(location_type):
    
    with open(project_dir + 'RJFAF214/RJFAF214.LOC', newline = '') as f:
        reader = csv.reader(f)
        for row in reader:
    
            if "Records" in row[0]:
                number_rows = int(re.findall(r'\d+', row[0])[0])
                break
    
    location_df = pd.read_csv(project_dir + 'RJFAF214/RJFAF214.LOC', skiprows = 6, nrows = number_rows, names = ['col'])
    
    if location_type == 'location record':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 289) and (x[1] == 'L'))]
    
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'uic_code': location_record['col'].str[2:9],
                             'end_date': location_record['col'].str[9:17],
                             'start_date': location_record['col'].str[17:25],
                             'quote_date': location_record['col'].str[25:33],
                             'admin_area_code': location_record['col'].str[33:36],
                             'nlc_code': location_record['col'].str[36:40],
                             'description': location_record['col'].str[40:56],
                             'crs_code': location_record['col'].str[56:59],
                             'resv_code': location_record['col'].str[59:64],
                             'ers_counry': location_record['col'].str[64:66],
                             'ers_code': location_record['col'].str[66:69],
                             'fare_group': location_record['col'].str[69:75],
                             'county': location_record['col'].str[75:77:],
                             'pte_code': location_record['col'].str[77:79],
                             'zone_no': location_record['col'].str[79:83],
                             'zone_ind': location_record['col'].str[83:85],
                             'region': location_record['col'].str[85],
                             'hierarchy': location_record['col'].str[86],
                             'cc_desc_out': location_record['col'].str[87:128],
                             'cc_desc_rtn': location_record['col'].str[128:144],
                             'atb_desc_out': location_record['col'].str[144:204],
                             'atb_desc_rtn': location_record['col'].str[204:234],
                             'special_facilities': location_record['col'].str[234:260],
                             'lul_direction_ind': location_record['col'].str[260],
                             'lul_uts_mode': location_record['col'].str[261],
                             'lul_zone_1': location_record['col'].str[262],
                             'lul_zone_2': location_record['col'].str[263],
                             'lul_zone_3': location_record['col'].str[264],
                             'lul_zone_4': location_record['col'].str[265],
                             'lul_zone_5': location_record['col'].str[266],
                             'lul_zone_6': location_record['col'].str[267],
                             'lul_uts_london_stn': location_record['col'].str[268],
                             'uts_code': location_record['col'].str[269:272],
                             'uts_a_code': location_record['col'].str[272:275],
                             'uts_ptr_bias': location_record['col'].str[275],
                             'uts_offset': location_record['col'].str[276],
                             'uts_north': location_record['col'].str[277:280],
                             'uts_east': location_record['col'].str[280:283],
                             'uts_south': location_record['col'].str[283:286],
                             'uts_west': location_record['col'].str[286:289]})
    
    if location_type == 'associated stations':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 27) and (x[1] == 'A'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'uic_code': location_record['col'].str[2:9],
                             'end_date': location_record['col'].str[9:17],
                             'assoc_uic_code': location_record['col'].str[17:24],
                             'assoc_crs_code': location_record['col'].str[24:27]})
    
    if location_type == 'railcard geography':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 20) and (x[1] == 'R'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'uic_code': location_record['col'].str[2:9],
                             'railcard_code': location_record['col'].str[9:12],
                             'end_date': location_record['col'].str[12:20]})
    
    if location_type == 'tt group location':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 54) and (x[1] == 'G'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'group_uic_code': location_record['col'].str[2:9],
                             'end_date': location_record['col'].str[9:17],
                             'start_date': location_record['col'].str[17:25],
                             'quote_date': location_record['col'].str[25:33],
                             'description': location_record['col'].str[33:49],
                             'ers_country': location_record['col'].str[49:51],
                             'ers_code': location_record['col'].str[51:54]})
    
    if location_type == 'group members':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 27) and (x[1] == 'M'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'group_uic_code': location_record['col'].str[2:9],
                             'end_date': location_record['col'].str[9:17],
                             'member_uic_code': location_record['col'].str[17:24],
                             'members_crs_code': location_record['col'].str[24:27]})
    
    if location_type == 'synonym record':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 41) and (x[1] == 'S'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'uic_code': location_record['col'].str[2:9],
                             'end_date': location_record['col'].str[9:17],
                             'start_date': location_record['col'].str[17:25],
                             'description': location_record['col'].str[25:41]})




















