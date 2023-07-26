import pandas as pd
import geopandas as gpd
import csv
import re
import string
# import contextily as cx
import folium
import json
from warnings import warn
import pkg_resources


#DEPRECATED
def get_nlc_codes():

    url_str = 'http://www.railwaycodes.org.uk/crs/crs'

    list_of_letters = list(string.ascii_lowercase)

    nlc_codes = pd.DataFrame(columns = ['Location', 'CRS', 'NLC', 'TIPLOC', 'STANME', 'STANOX'])

    for i in list_of_letters:
        
        full_url = url_str + i + '.shtm'
        
        html_tab = pd.read_html(full_url)
        df = html_tab[1]
        df.columns = html_tab[0].columns.values
        nlc_codes = pd.concat([nlc_codes, df])
        
    return nlc_codes



def get_station_clusters(project_dir):
    '''
    Retrieves station clusters from ATOC data.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    Pandas dataframe
        A data frame containing the station clusters data.

    '''
    
    stream = pkg_resources.resource_filename(__package__, 'RJFAF214/RJFAF214.FSC')
    
    with open(stream, "r", newline = '') as f:
        reader = csv.reader(f)
        for row in reader:
            if "Records" in row[0]:
                number_rows = int(re.findall(r'\d+', row[0])[0])
                break
            
    

    station_clusters = pd.read_csv(stream, skiprows = 6, nrows = number_rows, names = ['col'])
    
    return pd.DataFrame({'update-marker': station_clusters['col'].str[0],
                   'cluster_id': station_clusters['col'].str[1:5],
                   'cluster_nlc': station_clusters['col'].str[5:9],
                   'end_date': station_clusters['col'].str[9:17],
                   'start_date': station_clusters['col'].str[17:25]})

def get_cluster_from_nlc(nlc_code, project_dir, end_date = '31122999'):
    '''
    Given a station NLC code, find all clusters that station is part of.

    Parameters
    ----------
    nlc_code : STRING
        The NLC code of a station. Note, this should not be an NLC code of a cluster.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    end_date : STRING, optional
        The date until which the retrieved cluster is valid. The default is '31122999'.

    Returns
    -------
    Pandas dataframe
        A data frame containing all the clusters which contain the input station.

    '''
    
    station_clusters = get_station_clusters(project_dir)
    
    return station_clusters[(station_clusters['cluster_nlc'] == nlc_code) & (station_clusters['end_date'] == end_date)].reset_index()

def get_nlc_from_cluster(cluster_id, project_dir, end_date = '31122999'):
    '''
    Given a cluster NLC code, find all stations which are part of it.

    Parameters
    ----------
    cluster_id : STRING
        The NLC code identifying a cluster of stations.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    end_date : STRING, optional
        The date until which the retrieved cluster is valid. The default is '31122999'.

    Returns
    -------
    Pandas dataframe
        A data frame containing all the stations contained in the input cluster.

    '''
    
    station_clusters = get_station_clusters(project_dir)
    
    if not isinstance(cluster_id, pd.Series):
        
        cluster_id = [cluster_id]
    
    return station_clusters[(station_clusters['cluster_id'].isin(cluster_id)) & (station_clusters['end_date'] == end_date)].reset_index()

def get_cluster_nlc_dict(project_dir,  end_date = '31122999'):
    '''
    Create a dictionary of the station clusters to individual station correspondence.

    Parameters
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    end_date : STRING, optional
        The date until which the retrieved cluster is valid. The default is '31122999'.

    Returns
    -------
    DICT
        A dictionary with cluster NLC codes as keys, and station NLC codes as values.
        For each key (cluster NLC code), the values are a list of the stations (NLC codes)
        contained in that cluster. 

    '''
    
    station_clusters = get_station_clusters(project_dir)
    
    stations_clusters_active = station_clusters[station_clusters['end_date'] == end_date][['cluster_id', 'cluster_nlc']]
    
    return stations_clusters_active.groupby('cluster_id')['cluster_nlc'].apply(list).to_dict()


def get_all_station_nlc_codes(project_dir, print_progress = False, outpath = None):
    '''
    Creates a dictionary of the station name to station NLC codes correspondence.
    Note, there are multiple NLC codes associated to each station due to the
    existence of station clusters.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    print_progress : BOOLEAN, optional
        Whether the function prints progress updates throughout. The default is False.
    outpath : STRING, optional
        A path where the file can be saved. The default is None.

    Returns
    -------
    stations_nlc_dict : DICT
        A dictionary containing all NLC codes, including those of clusters, associated
        with an individual station. The keys are station names, and the values are
        all corresponding NLC codes associated to that station. NOTE: if outpath
        is different from None, the function does not return anything and saves
        the dictionary to file instead.

    '''
    
    loc_records_df = get_location_records('location record', project_dir)
    
    flow_df = get_flow_records('flow', project_dir)
    dest = loc_records_df[loc_records_df['nlc_code'].isin(flow_df['destination_code'].to_list())]['nlc_code'].unique()
    orig = loc_records_df[loc_records_df['nlc_code'].isin(flow_df['origin_code'].to_list())]['nlc_code'].unique()
    joint = list(orig) + list(set(dest) - set(orig))
    all_stations_nlcs = loc_records_df[(loc_records_df['nlc_code'].isin(joint)) & (loc_records_df['end_date'] == '31122999')].reset_index()

    stations_nlc_dict = {}

    for idx, row in all_stations_nlcs.iterrows():
        
        stations_codes = get_cluster_from_nlc(row['nlc_code'], project_dir)['cluster_id'].to_list()
        stations_codes.append(row['nlc_code'])
        stations_nlc_dict[row['description'].rstrip()] = stations_codes
        
        if print_progress:
            
            print('Step ', idx, 'out of ', len(all_stations_nlcs))
            
    if outpath != None:
        
        with open(outpath + '.json', 'w') as fp:
            json.dump(stations_nlc_dict, fp)
    else:
        
        return stations_nlc_dict

def get_all_station_crs_codes(project_dir, print_progress = False, outpath = None, end_date = '31122999'):
    '''
    Creates a dictionary of the station name to station CRS code correspondence.
    Note, not all stations have a station CRS code.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    print_progress : BOOLEAN, optional
        Whether the function prints progress updates throughout. The default is False.
    outpath : STRING, optional
        A path where the file can be saved. The default is None.
    end_date : STRING, optional
        A string representing the validity date until which a station is valid.
        Stations whose end date is different from the input are discarded.
        The default is '31122999'.

    Returns
    -------
    stations_crs_dict : DICT
        A dictionary containing the CRS code associated to each station (which has one).
        The keys of the dictionary are the station names, the values the corresponding
        CRS codes. NOTE: if outpath
        is different from None, the function does not return anything and saves
        the dictionary to file instead.

    '''
    
    loc_records_df = get_location_records('location record', project_dir)
    
    flow_df = get_flow_records('flow', project_dir)
    dest = loc_records_df[loc_records_df['nlc_code'].isin(flow_df['destination_code'].to_list())]['crs_code'].unique()
    orig = loc_records_df[loc_records_df['nlc_code'].isin(flow_df['origin_code'].to_list())]['crs_code'].unique()
    joint = list(orig) + list(set(dest) - set(orig))
    all_stations_crs = loc_records_df[(loc_records_df['crs_code'].isin(joint)) & (loc_records_df['end_date'] == '31122999')].reset_index()
    
    group_name_to_station_name_dict = station_group_to_stations_names_dict(project_dir)
    group_to_station_dict = get_station_group_dictionary(project_dir)
    group_name_to_uic = group_name_to_group_uic(project_dir, end_date)
    uic_to_names = uic_to_station_name_dict(project_dir)
    
    stations_crs_dict = {}

    for idx, row in all_stations_crs.iterrows():
        
        if not row['crs_code'].isspace():
            
            stations_crs_dict[row['description'].rstrip()] = row['crs_code']
        
        elif (row['crs_code'].isspace()) and (row['description'].rstrip() in group_name_to_station_name_dict.keys()):
            
            stations_list = group_to_station_dict[group_name_to_uic[row['description'].rstrip()]]
            
            for x in stations_list:
                
                station_name = uic_to_names[x['member_uic_code']]
                
                if not station_name in stations_crs_dict.keys():
                    
                    stations_crs_dict[station_name] = x['members_crs_code']
        else:
            
            stations_crs_dict[row['description'].rstrip()] = row['crs_code']
            
        if print_progress:
            
            print('Step ', idx, 'out of ', len(all_stations_crs))
            
    if outpath != None:
        
        with open(outpath + '.json', 'w') as fp:
            json.dump(stations_crs_dict, fp)
    else:
        
        return stations_crs_dict
        
def get_location_records(location_type, project_dir):
    '''
    Parses the location records file of the ATOC fares data.

    Parameters
    ----------
    location_type : STRING
        The type of location records to be parsed.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
        
    Returns
    -------
    Pandas dataframe
        A data frame containing the requested location records.

    '''
    
    with open(project_dir + 'RJFAF495/RJFAF495.LOC', newline = '') as f:
        reader = csv.reader(f)
        for row in reader:
    
            if "Records" in row[0]:
                number_rows = int(re.findall(r'\d+', row[0])[0])
                break
    
    location_df = pd.read_csv(project_dir + 'RJFAF495/RJFAF495.LOC', skiprows = 6, nrows = number_rows, names = ['col'])
    
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
                             'ers_country': location_record['col'].str[64:66],
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
                             'uts_west': location_record['col'].str[286:289]}).reset_index()
    
    if location_type == 'associated stations':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 27) and (x[1] == 'A'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'uic_code': location_record['col'].str[2:9],
                             'end_date': location_record['col'].str[9:17],
                             'assoc_uic_code': location_record['col'].str[17:24],
                             'assoc_crs_code': location_record['col'].str[24:27]}).reset_index()
    
    if location_type == 'railcard geography':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 20) and (x[1] == 'R'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'uic_code': location_record['col'].str[2:9],
                             'railcard_code': location_record['col'].str[9:12],
                             'end_date': location_record['col'].str[12:20]}).reset_index()
    
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
                             'ers_code': location_record['col'].str[51:54]}).reset_index()
    
    if location_type == 'group members':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 27) and (x[1] == 'M'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'group_uic_code': location_record['col'].str[2:9],
                             'end_date': location_record['col'].str[9:17],
                             'member_uic_code': location_record['col'].str[17:24],
                             'members_crs_code': location_record['col'].str[24:27]}).reset_index()
    
    if location_type == 'synonym record':
        
        location_record = location_df[location_df['col'].apply(lambda x: (len(x) == 41) and (x[1] == 'S'))]
        
        return pd.DataFrame({'update_marker': location_record['col'].str[0],
                             'record_type': location_record['col'].str[1],
                             'uic_code': location_record['col'].str[2:9],
                             'end_date': location_record['col'].str[9:17],
                             'start_date': location_record['col'].str[17:25],
                             'description': location_record['col'].str[25:41]}).reset_index()


def get_station_group_dictionary(project_dir, end_date = '31122999'):
    '''
    Create a dictionary with the correspondence of station group UIC codes with
    the station members UIC and CRS codes.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    end_date : STRING, optional
        A string representing the validity date until which a station group is valid.
        Station groups whose end date is different from the input are discarded.
        The default is '31122999'.

    Returns
    -------
    outdict : DICT
        A dictionary with the association of a station group UIC code with the
        UIC and CRS codes of the group members. Keys are the station group UIC
        codes, and the values are a nested dictionary for each station member of that
        group. The nested dictionary contains the following keys: 'member_uic_code'
        and 'members_crs_code', representing each station's UIC and CRS code respectively.'
        Note that a station could in principle be part of multiple groups.

    '''
    
    station_groups = get_location_records('group members', project_dir)
    
    stations_groups_active = station_groups[station_groups['end_date'] == end_date][['group_uic_code', 'member_uic_code', 'members_crs_code']]
    
    
    
    outdict = {} # create output dictionary

    df = stations_groups_active.set_index('group_uic_code') # set index and group
    df_grouped = df.groupby(df.index)

    #iterate through groups populating the dictionary
    for grp in df_grouped.groups:
        g = df_grouped.get_group(grp)
        outdict[grp] = g.to_dict('records')
    
    return outdict

def fares_group_to_uic_dict(project_dir, end_date = '31122999'):
    '''
    Create a dictionary with the association of the fare group NLC code and the
    group UIC code.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    end_date : STRING, optional
        A string representing the validity date until which a station group is valid.
        Station groups whose end date is different from the input are discarded.
        The default is '31122999'.

    Returns
    -------
    DICT
        A dictionary to link fare group NLC codes to group UIC codes. Keys are
        the fare group NLC codes, and values the corresponding UIC code for the
        group.

    '''
    
    group_members_dict = get_station_group_dictionary(project_dir, end_date = '31122999')
    group_keys = group_members_dict.keys()
    
    loc_records_df = get_location_records('location record', project_dir)
    
    group_stations = loc_records_df[(loc_records_df['uic_code'].isin(group_keys)) & (loc_records_df['end_date'] == '31122999')].copy()
    
    group_stations['fare_group'] = group_stations['fare_group'].str.rstrip()
    
    return group_stations.set_index('fare_group').to_dict()['uic_code']

def group_name_to_group_uic(project_dir, end_date = '31122999'):
    '''
    Create a dictionary with the correspondence of station group names to station
    group UIC codes.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    end_date : STRING, optional
        A string representing the validity date until which a station group is valid.
        Station groups whose end date is different from the input are discarded.
        The default is '31122999'.

    Returns
    -------
    DICT
        A dictionary linking station group names to station group UIC codes.
        Keys are the station group names, and values the corresponding UIC codes.

    '''
    
    group_members_dict = get_station_group_dictionary(project_dir, end_date = '31122999')
    group_keys = group_members_dict.keys()
    
    loc_records_df = get_location_records('location record', project_dir)
    
    group_stations = loc_records_df[(loc_records_df['uic_code'].isin(group_keys)) & (loc_records_df['end_date'] == '31122999')].copy()
    
    group_stations['description'] = group_stations['description'].str.rstrip()
    
    return group_stations.set_index('description').to_dict()['uic_code']

def uic_to_station_name_dict(project_dir, end_date = '31122999'):
    '''
    Create a dictionary with the correspondence between station UIC code and
    the station name.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    end_date : STRING, optional
        A string representing the validity date until which a station group is valid.
        Station groups whose end date is different from the input are discarded.
        The default is '31122999'.

    Returns
    -------
    DICT
        A dictionary linking station UIC code and its name. Keys are the UIC codes
        and values are the station names.

    '''
    
    loc_records_df =  get_location_records('location record', project_dir)
    
    active_locs = loc_records_df[loc_records_df['end_date'] == end_date][['uic_code', 'description']].copy()
    
    active_locs['description'] = active_locs['description'].str.rstrip()
    
    return active_locs.set_index('uic_code').to_dict()['description']
    

def station_group_to_stations_names_dict(project_dir, end_date = '31122999'):
    '''
    Create a dictionary with the correspondence between station group name and
    the names of stations contained within that group.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    end_date : STRING, optional
        A string representing the validity date until which a station group is valid.
        Station groups whose end date is different from the input are discarded.
        The default is '31122999'.

    Returns
    -------
    group_to_names_dict : DICT
        A dictionary linking the station group name to the names of the stations
        contained within that group. Keys are the station group names, values are
        the names of the stations within that group. Note that in principle a station
        can appear in multiple station groups..

    '''
    
    uic_to_station_name = uic_to_station_name_dict(project_dir, end_date)
    fares_group_to_uic = fares_group_to_uic_dict(project_dir, end_date)
    station_group_dict = get_station_group_dictionary(project_dir, end_date)
    
    
    loc_records_df = get_location_records('location record', project_dir)[['description', 'fare_group', 'end_date', 'uic_code']]
    loc_records_df['fare_group'] = loc_records_df['fare_group'].str.rstrip()
    loc_records_df['description'] = loc_records_df['description'].str.rstrip()
    loc_records_df = loc_records_df[loc_records_df['end_date'] == end_date]
    group_codes_values = loc_records_df[(loc_records_df['fare_group'].isin(fares_group_to_uic.keys())) & (loc_records_df['uic_code'].isin(fares_group_to_uic.values()))].drop(columns = 'end_date', axis = 1)
    
    group_nlc_to_name = group_codes_values.set_index('fare_group').to_dict()['description']
    
    
    
    group_to_names_dict = {}
    
    for key, value in fares_group_to_uic.items():
        
        stns = []
        for value1 in station_group_dict[value]:
            
            stns.append(uic_to_station_name[value1['member_uic_code']])
            
        group_to_names_dict[group_nlc_to_name[key]] = stns
        
    return group_to_names_dict


def get_flow_records(flow_type, project_dir):
    '''
    Parse the flow records of the ATOC fares data.

    Parameters
    ----------
    flow_type : STRING
        A string containing the type of record to be retrieved. Can be either
        "flow" for the flows, or "fares" for the fares.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    Pandas data frame
        A data frame containing the requested flow or fares data.

    '''
    
    with open(project_dir + 'RJFAF495/RJFAF495.FFL', newline = '') as f:
        reader = csv.reader(f)
        for row in reader:
    
            if "Records" in row[0]:
                number_rows = int(re.findall(r'\d+', row[0])[0])
                break
    
    flow_df = pd.read_csv(project_dir + 'RJFAF495/RJFAF495.FFL', skiprows = 6, nrows = number_rows, names = ['col'])
    
    if flow_type == 'flow':
        
        flow_record = flow_df[flow_df['col'].apply(lambda x: (len(x) == 49) and (x[1] == 'F'))]
        
        return pd.DataFrame({'update-marker':flow_record['col'].str[0],
                             'record_type':flow_record['col'].str[1],
                             'origin_code':flow_record['col'].str[2:6],
                             'destination_code':flow_record['col'].str[6:10],
                             'route_code':flow_record['col'].str[10:15],
                             'status_code':flow_record['col'].str[15:18],
                             'usage_code':flow_record['col'].str[18],
                             'direction':flow_record['col'].str[19],
                             'end_date':flow_record['col'].str[20:28],
                             'start_date':flow_record['col'].str[28:36],
                             'toc':flow_record['col'].str[36:39],
                             'cross_london_ind':flow_record['col'].str[39],
                             'ns_disc_ind':flow_record['col'].str[40],
                             'publication_ind':flow_record['col'].str[41],
                             'flow_id':flow_record['col'].str[42:49]})
        
    if flow_type == 'fares':
        
        fare_record = flow_df[flow_df['col'].apply(lambda x: (len(x) == 22) and (x[1] == 'T'))]
        
        return pd.DataFrame({'update-marker':fare_record['col'].str[0],
                             'record_type':fare_record['col'].str[1],
                             'flow_id':fare_record['col'].str[2:9],
                             'ticket_code':fare_record['col'].str[9:12],
                             'fare':fare_record['col'].str[12:20],
                             'restriction_code':fare_record['col'].str[20:22]})
    
    if flow_type == 'both':
        
        flow_record = flow_df[flow_df['col'].apply(lambda x: (len(x) == 49) and (x[1] == 'F'))]
        fare_record = flow_df[flow_df['col'].apply(lambda x: (len(x) == 22) and (x[1] == 'T'))]
        
        return pd.DataFrame({'update-marker':flow_record['col'].str[0],
                             'record_type':flow_record['col'].str[1],
                             'origin_code':flow_record['col'].str[2:6],
                             'destination_code':flow_record['col'].str[6:10],
                             'route_code':flow_record['col'].str[10:15],
                             'status_code':flow_record['col'].str[15:18],
                             'usage_code':flow_record['col'].str[18],
                             'direction':flow_record['col'].str[19],
                             'end_date':flow_record['col'].str[20:28],
                             'start_date':flow_record['col'].str[28:36],
                             'toc':flow_record['col'].str[36:39],
                             'cross_london_ind':flow_record['col'].str[39],
                             'ns_disc_ind':flow_record['col'].str[40],
                             'publication_ind':flow_record['col'].str[41],
                             'flow_id':flow_record['col'].str[42:49]}),pd.DataFrame({'update-marker':fare_record['col'].str[0],
                                                  'record_type':fare_record['col'].str[1],
                                                  'flow_id':fare_record['col'].str[2:9],
                                                  'ticket_code':fare_record['col'].str[9:12],
                                                  'fare':fare_record['col'].str[12:20],
                                                  'restriction_code':fare_record['col'].str[20:22]})



def get_ticket_type_records(project_dir):
    '''
    Parse the ticket type records of the ATOC fares data.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    Pandas dataframe
        A data frame containing the requested ticket type data.

    '''
    
    with open(project_dir + 'RJFAF495/RJFAF495.TTY', newline = '') as f:
        reader = csv.reader(f)
        for row in reader:
    
            if "Records" in row[0]:
                number_rows = int(re.findall(r'\d+', row[0])[0])
                break
    
    ticket_df = pd.read_csv(project_dir + 'RJFAF495/RJFAF495.TTY', skiprows = 6, nrows = number_rows, names = ['col'])
    
    return pd.DataFrame({'update_marker': ticket_df['col'].str[0],
                         'ticket_code': ticket_df['col'].str[1:4],
                         'end_date': ticket_df['col'].str[4:12],
                         'start_date': ticket_df['col'].str[12:20],
                         'quote_date': ticket_df['col'].str[20:28],
                         'description': ticket_df['col'].str[28:43],
                         'tkt_class': ticket_df['col'].str[43],
                         'tkt_type': ticket_df['col'].str[44],
                         'tkt_group': ticket_df['col'].str[45],
                         'last_valid_day': ticket_df['col'].str[46:54],
                         'max_passengers': ticket_df['col'].str[54:57],
                         'min_passengers': ticket_df['col'].str[57:60],
                         'max_adults': ticket_df['col'].str[60:63],
                         'min_adults': ticket_df['col'].str[63:66],
                         'max_children': ticket_df['col'].str[66:69],
                         'min_children': ticket_df['col'].str[69:72],
                         'restricted_by_date': ticket_df['col'].str[72],
                         'restricted_by_train': ticket_df['col'].str[73],
                         'restricted_by_area': ticket_df['col'].str[74],
                         'validity_code': ticket_df['col'].str[75:77],
                         'atb_description': ticket_df['col'].str[77:97],
                         'lul_xlondon_issue': ticket_df['col'].str[97],
                         'reservation_required': ticket_df['col'].str[98],
                         'capri_code': ticket_df['col'].str[99:102],
                         'lul_93': ticket_df['col'].str[102],
                         'uts_code': ticket_df['col'].str[103:105],
                         'time_restriction': ticket_df['col'].str[105],
                         'free_pass_lul': ticket_df['col'].str[106],
                         'package_mkr': ticket_df['col'].str[107],
                         'fare_multiplier': ticket_df['col'].str[108:111],
                         'discount_category': ticket_df['col'].str[111:113]})


def get_ticket_validity(project_dir):
    '''
    Parse the ticket validity records of the ATOC fares data.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    Pandas dataframe
        A data frame containining the requested ticket validity data.

    '''
    
    with open(project_dir + 'RJFAF495/RJFAF495.TVL', newline = '') as f:
        reader = csv.reader(f)
        for row in reader:
    
            if "Records" in row[0]:
                number_rows = int(re.findall(r'\d+', row[0])[0])
                break
    
    validity_df = pd.read_csv(project_dir + 'RJFAF495/RJFAF495.TVL', skiprows = 6, nrows = number_rows, names = ['col'])
    
    return pd.DataFrame({'validity_code': validity_df['col'].str[0:2],
                         'end_date': validity_df['col'].str[2:10],
                         'start_date': validity_df['col'].str[10:18],
                         'description': validity_df['col'].str[18:38],
                         'out_days': validity_df['col'].str[38:40],
                         'out_months': validity_df['col'].str[40:42],
                         'ret_days': validity_df['col'].str[42:44],
                         'ret_months': validity_df['col'].str[44:46],
                         'ret_after_days': validity_df['col'].str[46:48],
                         'ret_after_months': validity_df['col'].str[48:50],
                         'ret_after_day': validity_df['col'].str[50:52],
                         'break_out': validity_df['col'].str[52],
                         'break_rtn': validity_df['col'].str[53],
                         'out_description': validity_df['col'].str[54:68],
                         'rtn_description': validity_df['col'].str[68:82]})

def get_station_location(project_dir, tiploc = False):
    '''
    Parse the station location records from the ATOC timetable data.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    tiploc : BOOLEAN, optional
        A boolean variable indicating whether the TIPLOC codes associated with 
        each station should be returned. The default is False.

    Returns
    -------
    Geopandas dataframe
        A geo-data frame containing the requested location data. The geo-data
        frame is in the following CRS: OSGB36 / British National Grid.

    '''
    
    
    timetable = pd.read_csv(project_dir + 'ttis418/ttisf418.msn', skiprows = 1, names = ['col'])
    

    station_locations = timetable[timetable['col'].apply(lambda x: (len(x) == 82) and (x[0] == 'A'))]
    
    if not tiploc:
        
        station_df = pd.DataFrame({'Station name':station_locations['col'].str[5:31].str.rstrip(), 
                                   'CRS Code': station_locations['col'].str[49:52],
                                   'Minor CRS code': station_locations['col'].str[43:46]})
    elif tiploc:
        
        station_df = pd.DataFrame({'Station name':station_locations['col'].str[5:31].str.rstrip(), 
                                   'tiploc_code': station_locations['col'].str[36:43],
                                   'CRS Code': station_locations['col'].str[49:52],
                                   'Minor CRS code': station_locations['col'].str[43:46]})
        station_df['tiploc_code'] = station_df['tiploc_code'].str.rstrip()
        
    station_points = gpd.points_from_xy(station_locations['col'].str[53:57] + '00', station_locations['col'].str[59:63] + '00',  crs = 'OSGB36 / British National Grid')
    
    return gpd.GeoDataFrame(station_df, geometry = station_points)

def get_naptan_data(project_dir):
    '''
    Parse the NAPTAN data containing the location of all stations. This is an
    alternative to using the location data contained in the ATOC timetable files.

    Parameters
    ----------
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    Geopandas dataframe
        A geo-data frame containing the station location data. The geo-data frame
        is in the following CRS: OSGB36 / British National Grid.

    '''
    
    naptan_data = pd.read_csv(project_dir + 'naptan_data.csv', low_memory = False)[['ATCOCode', 'CommonName', 'Easting', 'Northing', 'Longitude', 'Latitude', 'StopType']]
    
    naptan_rail = naptan_data[naptan_data['StopType'] == 'RLY'].copy()
    
    naptan_rail['TIPLOC'] = naptan_rail['ATCOCode'].apply(lambda x: x[4:])
    
    naptan_rail.drop(columns = ['ATCOCode', 'StopType'], axis = 1, inplace = True)
    
    points = gpd.points_from_xy(naptan_rail['Easting'], naptan_rail['Northing'], crs = 'OSGB36 / British National Grid')
    
    return gpd.GeoDataFrame(naptan_rail, geometry = points)
    

def get_station_code_from_name(station_name, project_dir):
    '''
    Retrieve station NLC and CRS codes from station name.

    Parameters
    ----------
    station_name : STRING
        The name of a train station.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    Pandas data frame
        A data frame containing the NLC and CRS codes for the input station name.
        Note that if no match is found for the input station name, the function
        returns an empty data frame.

    '''
    
    station_name = station_name.lower()
    
    station_gdf = get_station_location(project_dir)
    
    station_crs = station_gdf[station_gdf['Station name'].str.lower().str.contains(station_name, regex = False)][['Station name', 'CRS Code', 'Minor CRS code']]
    
    loc_records_df = get_location_records('location record', project_dir)[['nlc_code', 'crs_code']]
    
    return station_crs.merge(loc_records_df, left_on = 'CRS Code', right_on = 'crs_code', how = 'left').drop_duplicates()

def get_station_name_from_code(station_code, project_dir):
    '''
    Retrieve station name from station NLC code.

    Parameters
    ----------
    station_code : STRING
        A station NLC code. NOTE: this can also be a collection of strings
        contained in a Pandas series.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    Pandas dataframe
        A data frame containing the association between station code and name.
        If the input is a collection of strings, each row of the data frame
        corresponds to one of the input station NLC codes.

    '''
    warn('This is deprecated', DeprecationWarning, stacklevel = 2)
    if not isinstance(station_code, pd.Series):
        
        station_code = [station_code]
    
    station_gdf = get_station_location(project_dir)
    
    loc_records_df = get_location_records('location record', project_dir)[['nlc_code', 'crs_code']]
    
    station_nlc = loc_records_df[loc_records_df['nlc_code'].apply(lambda x: any([str(k) in x for k in station_code]))].drop_duplicates()
    
    return station_gdf.merge(station_nlc, left_on = 'CRS Code', right_on = 'crs_code', how = 'inner')

def get_isocost_from_list(station_flows_df, isocost, project_dir, inverse = False):
    '''
    Associates fares to flows from a specific station.

    Parameters
    ----------
    station_flows_df : Pandas dataframe
        A data frame containing the flows corresponding to a specific starting station.
    isocost : Pandas dataframe
        A data frame containing the fares data for flows starting from a specific
        station.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    inverse : BOOLEAN, optional
        Whether we are looking at reverse flows. The default is False.

    Returns
    -------
    Pandas dataframe
        A data frame containing the flows and associated fares. Station clusters
        are disaggregated in the component stations of the cluster.

    '''
    
    temp_isocost_route = station_flows_df[(station_flows_df['flow_id'].isin(isocost['flow_id'].to_list())) & (station_flows_df['end_date'] == '31122999')].copy()
    
    if not inverse:
        
        temp_isocost_route['bool'] = [get_nlc_from_cluster(x, project_dir).empty for x in temp_isocost_route['destination_code']]
        stations_route = temp_isocost_route[temp_isocost_route['bool'] == True]
        clusters_route = temp_isocost_route[temp_isocost_route['bool'] == False]
        unique_clusters = pd.Series(clusters_route['destination_code'].unique())
        disagr_clusters = clusters_route.merge(get_nlc_from_cluster(pd.Series(unique_clusters),project_dir)[['cluster_id', 'cluster_nlc']], left_on = 'destination_code', right_on = 'cluster_id')
        isocost_route = pd.concat([stations_route, disagr_clusters])
        isocost_route['cluster_nlc'].fillna(isocost_route['destination_code'], inplace = True)
    
    elif inverse:
        
        temp_isocost_route['bool'] = [get_nlc_from_cluster(x, project_dir).empty for x in temp_isocost_route['destination_code']]
        stations_route = temp_isocost_route[temp_isocost_route['bool'] == True]
        clusters_route = temp_isocost_route[temp_isocost_route['bool'] == False]
        unique_clusters = pd.Series(clusters_route['origin_code'].unique())
        disagr_clusters = clusters_route.merge(get_nlc_from_cluster(pd.Series(unique_clusters),project_dir)[['cluster_id', 'cluster_nlc']], left_on = 'origin_code', right_on = 'cluster_id')
        isocost_route = pd.concat([stations_route, disagr_clusters])
        isocost_route['cluster_nlc'].fillna(isocost_route['origin_code'], inplace = True)
        
    isocost_destinations = get_station_name_from_code(isocost_route['cluster_nlc'], project_dir)
    isocost_fare = isocost_route.merge(isocost[['flow_id','fare']], left_on = 'flow_id', right_on = 'flow_id', how = 'left')
    return isocost_destinations.merge(isocost_fare, left_on = 'nlc_code', right_on = 'cluster_nlc')


def get_isocost_from_list_fast(station_flows_df, isocost, station_gdf, loc_records_df, clusters_dict, project_dir, inverse = False):
    '''
    Same as get_isocost_from_list but faster.

    Parameters
    ----------
    station_flows_df : Pandas dataframe
        A data frame containing the flows corresponding to a specific starting station.
    isocost : Pandas dataframe
        A data frame containing the fares data for flows starting from a specific
        station.
    station_gdf : Geopandas dataframe.
        A geo-data frame containing the stations.
    loc_records_df : Pandas dataframe.
        A data frame containing the location records retrieved from get_location_records('location record', project_dir).
    clusters_dict : DICT
        A dictionary linking station clusters to individual stations.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.
    inverse : BOOLEAN, optional
        Whether we are looking at reverse flows. The default is False.

    Returns
    -------
    Pandas dataframe
        A data frame containing the flows and associated fares. Station clusters
        are disaggregated in the component stations of the cluster.

    '''
    
    temp_isocost_route = station_flows_df[(station_flows_df['flow_id'].isin(isocost['flow_id'].to_list())) & (station_flows_df['end_date'] == '31122999')]
    
    # clusters_dict = get_cluster_nlc_dict(project_dir)
    
    if not inverse:
        
        temp_isocost_route['bool'] = [x in clusters_dict for x in temp_isocost_route['destination_code']]
        stations_route = temp_isocost_route[temp_isocost_route['bool'] == False]
        clusters_route = temp_isocost_route[temp_isocost_route['bool'] == True]
        unique_clusters = pd.Series(clusters_route['destination_code'].unique())
        disagr_clusters = clusters_route.merge(get_nlc_from_cluster(pd.Series(unique_clusters),project_dir)[['cluster_id', 'cluster_nlc']], left_on = 'destination_code', right_on = 'cluster_id')
        isocost_route = pd.concat([stations_route, disagr_clusters])
        isocost_route['cluster_nlc'].fillna(isocost_route['destination_code'], inplace = True)
    
    elif inverse:
        
        temp_isocost_route['bool'] = [x in clusters_dict  for x in temp_isocost_route['destination_code']]
        stations_route = temp_isocost_route[temp_isocost_route['bool'] == False]
        clusters_route = temp_isocost_route[temp_isocost_route['bool'] == True]
        unique_clusters = pd.Series(clusters_route['origin_code'].unique())
        disagr_clusters = clusters_route.merge(get_nlc_from_cluster(pd.Series(unique_clusters),project_dir)[['cluster_id', 'cluster_nlc']], left_on = 'origin_code', right_on = 'cluster_id')
        isocost_route = pd.concat([stations_route, disagr_clusters])
        isocost_route['cluster_nlc'].fillna(isocost_route['origin_code'], inplace = True)
        
    # isocost_destinations = get_station_name_from_code(isocost_route['cluster_nlc'], project_dir)
    
    station_code = isocost_route['cluster_nlc']
    
    if not isinstance(station_code, pd.Series):
        
        station_code = [station_code]
    
    station_nlc = loc_records_df[loc_records_df['nlc_code'].apply(lambda x: any([str(k) in x for k in station_code]))].drop_duplicates()
    
    isocost_destinations = station_gdf.merge(station_nlc, left_on = 'CRS Code', right_on = 'crs_code', how = 'inner')
    
    isocost_fare = isocost_route.merge(isocost[['flow_id','fare']], left_on = 'flow_id', right_on = 'flow_id', how = 'left')
    return isocost_destinations.merge(isocost_fare, left_on = 'nlc_code', right_on = 'cluster_nlc')
    
    

def get_isocost_stations(starting_station, budget, project_dir):
    '''
    Calculates the isocost for a given starting station and budget.

    Parameters
    ----------
    starting_station : STRING
        The name of the starting station.
    budget : INTEGER
        The maximum budget to be used for calculating routes.
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    Pandas dataframe.
        A data frame containing all stations you can reach with a given budget
        starting from the input starting station. Actual fares of the routes
        are also included in the data frame.

    '''
    
    
    tickets = get_ticket_type_records(project_dir)
    
    validity = get_ticket_validity(project_dir)
    # val_code = validity[validity['out_days'] == '01']['validity_code'].to_list()
    val_code = validity['validity_code'].to_list()
    single_tickets = pd.DataFrame([x for idx, x in tickets.iterrows() if x['end_date'] == '31122999' and x['tkt_class'] == '2' and x['tkt_type'] == 'S' and x['validity_code'] in val_code and 'anytime' in x['description'].lower()])
    
    
    station_nlc = get_station_code_from_name(starting_station, project_dir)['nlc_code']
    stations_codes = get_cluster_from_nlc(station_nlc[0], project_dir)['cluster_id'].to_list()
    stations_codes.append(station_nlc[0])
    
    
    
    flow_df = get_flow_records('flow', project_dir)
    station_flows_df = flow_df[(flow_df['origin_code'].isin(stations_codes)) & (flow_df['end_date'] == '31122999')]
    fares_df = get_flow_records('fares', project_dir)
    station_list = station_flows_df['flow_id'].to_list()
    station_fares_df = fares_df[fares_df['flow_id'].isin(station_list)]
    # station_tickets = tickets[tickets['ticket_code'].isin(station_fares_df['ticket_code'].to_list())]
    station_singles = station_fares_df[station_fares_df['ticket_code'].isin(single_tickets['ticket_code'].to_list())].copy()
    station_singles['fare'] = station_singles['fare'].astype(int)/100
    
    #look if flows/routes exist in reverse direction
    inverse_station_flows_df = flow_df[(flow_df['destination_code'].isin(stations_codes)) & (flow_df['end_date'] == '31122999') & (flow_df['direction'] == 'R')]
    inverse_station_list = inverse_station_flows_df['flow_id'].to_list()
    inverse_station_fares_df = fares_df[fares_df['flow_id'].isin(inverse_station_list)]
    # inverse_station_tickets = tickets[tickets['ticket_code'].isin(inverse_station_fares_df['ticket_code'].to_list())]
    inverse_station_singles = inverse_station_fares_df[inverse_station_fares_df['ticket_code'].isin(single_tickets['ticket_code'].to_list())].copy()
    inverse_station_singles['fare'] = inverse_station_singles['fare'].astype(int)/100
    
    
    isocost = station_singles[station_singles['fare'].apply(lambda x: x <= budget)]
    destination_stations = get_isocost_from_list(station_flows_df, isocost, project_dir)
    
    
    #look at cost of routes in reverse direction
    inverse_isocost = inverse_station_singles[inverse_station_singles['fare'].apply(lambda x: x <= budget)]
    inverse_destination_stations = get_isocost_from_list(inverse_station_flows_df, inverse_isocost, project_dir, inverse = True)
    
    
    return pd.concat([destination_stations, inverse_destination_stations])
    

def plot_isocost_stations(starting_station_code, destination_stations, out_path, project_dir):
    '''
    Create an html map of the isocost from a station.

    Parameters
    ----------
    starting_station_code : STRING
        The starting station NLC code.
    destination_stations : Pandas dataframe
        A data frame containing all destination stations.
    out_path : STRING
        The path where the map will be saved..
    project_dir : STRING
        The directory where the project is hosted, needed for reading data files.

    Returns
    -------
    None.

    '''
    
    station_gdf = get_station_location(project_dir)
    station_gdf = station_gdf.to_crs(epsg = 4326)
    
    starting_gdf = station_gdf[station_gdf['CRS Code'] == starting_station_code]
    
    destination_gdf = station_gdf[station_gdf['CRS Code'].isin(destination_stations['crs_code'])]
    
    starting_gdf['label'] = 'starting'
    starting_gdf['fare'] = 0
    destination_gdf['label'] = 'destination'
    destination_gdf = destination_gdf.merge(destination_stations[['crs_code', 'fare']], left_on = 'CRS Code', right_on = 'crs_code')
    
    stats_gdf = starting_gdf.append(destination_gdf).reset_index()
    
    

    duplicate_stations = []
    
    
    cost_map = folium.Map(location = [stats_gdf.dissolve().centroid[0].coords[0][1],stats_gdf.dissolve().centroid[0].coords[0][0]], tiles = "https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiZmVkZWJvdHRhIiwiYSI6ImNsNnZzZmx1bDA0aXozYnA5NHNxc2oxYm4ifQ.NH-kHQqlCLP3OVnx5ygJlQ", attr = 'mapbox', zoom_start = 10)
    for idx, row in stats_gdf.iterrows():
        
        if row['Station name'] not in duplicate_stations:
            
            duplicate_stations.append(row['Station name'])
            
            stats_df = stats_gdf[stats_gdf['Station name'] == row['Station name']]
            
            if row['label'] == 'starting':
                
                type_color = 'green'
                
            elif row['label'] == 'destination':
                
                type_color = 'blue'
                
            fares_str = ''
            
            for idx1, row1 in stats_df.iterrows():
                
                fares_str = fares_str + '<br>' + '£' + str(row1['fare']).ljust(4,'0')
        
        cost_map.add_child(folium.Marker(location = [row['geometry'].xy[1][0], row['geometry'].xy[0][0]],
                                popup =
                                "Station: " + str(row['Station name']) + '<br>' +
                                "Fares: " + fares_str,
                                icon = folium.Icon(color = "%s" % type_color)))
    cost_map.save(out_path)




