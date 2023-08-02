import pandas as pd
import geopandas as gpd
import railfares.data_parsing as data_parsing
import matplotlib.pyplot as plt
from scipy.stats import kendalltau as kendall
from urllib.request import urlopen
import json

project_dir = '/Users/fb394/Documents/GitHub/railfares/'

#the next section is commented because the data has now been saved to file.
#Uncomment to recalculate.

od_list = pd.read_csv(project_dir + 'od_minimum_cost_matrix.csv', low_memory = False)

naptan_gdf = data_parsing.get_naptan_data(project_dir)
naptan_gdf = naptan_gdf.to_crs(epsg = 27700)


station_gdf = data_parsing.get_station_location(project_dir, tiploc = True)
station_gdf = station_gdf.to_crs(epsg = 4326)
stations = gpd.GeoDataFrame(naptan_gdf.merge(station_gdf, left_on = 'TIPLOC', right_on = 'tiploc_code', how = 'left').drop(columns = ['geometry_y', 'Easting', 'Northing'], axis = 1).rename(columns = {'geometry_x': 'geometry'})).dropna().drop_duplicates('CRS Code')
stations = stations.to_crs(epsg = 4326)


# lsoa_gdf = gpd.read_file('https://opendata.arcgis.com/datasets/1f23484eafea45f98485ef816e4fee2d_0.geojson')


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





stations_lsoa_gdf = lsoa_gdf.sjoin(stations)
stations_lsoa_gdf = stations_lsoa_gdf.to_crs(epsg = 27700)

# stations_lsoa_gdf['MeanFare'] = 0
# stations_lsoa_gdf['MedianFare'] = 0

stn_numbers = pd.DataFrame()

for idx, row in stations_lsoa_gdf.iterrows():
    
    # station_od = od_list[od_list['origin_crs'] == row['CRS Code']].copy()
    station_od = od_list.query('origin_crs==@row["CRS Code"]')
    
    if not station_od.empty:
        
        temp_gdf = stations_lsoa_gdf.merge(station_od, left_on = 'CRS Code', right_on = 'destination_crs')
        
        temp_gdf['distance'] = temp_gdf.geometry.apply(lambda x: row['geometry'].distance(x))
        
        stn_numbers = pd.concat([stn_numbers, pd.DataFrame([[row['LSOA11CD'], row['CRS Code'], temp_gdf['distance'].max(), temp_gdf['distance'].mean(),
                                                              temp_gdf['distance'].median(), temp_gdf['fare'].mean(), temp_gdf['fare'].median(), temp_gdf['fare'].max(), row['geometry']]],
                                                            columns = ['LSOA11CD', 'Station CRS', 'Max distance', 'Mean distance', 'Median distance', 
                                                                      'MeanFare', 'MedianFare', 'MaxFare', 'geometry'])])
        
        print(row['CRS Code'])

stn_numbers_gdf = gpd.GeoDataFrame(stn_numbers, crs = "EPSG:27700")

stn_numbers_gdf.to_file(project_dir + 'stations_lsoa_statistics.geojson', driver = 'GeoJSON')



stn_numbers_gdf = gpd.read_file(project_dir + 'stations_lsoa_statistics.geojson')

imd_df = pd.read_excel('https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/833978/File_5_-_IoD2019_Scores.xlsx', sheet_name = 'IoD2019 Scores')

stn_imd_gdf = stn_numbers_gdf.merge(imd_df, left_on = 'LSOA11CD', right_on = 'LSOA code (2011)')

rural_urban_df = pd.read_excel(project_dir + 'Rural_Urban_Classification_2011_lookup_tables_for_small_area_geographies.ods', engine = 'odf', sheet_name = 'LSOA11', skiprows = 2)

stn_imd_gdf = stn_imd_gdf.merge(rural_urban_df, left_on = 'LSOA11CD', right_on = 'Lower Super Output Area 2011 Code')

x_vars = ['Max distance', 
        'Median distance', 'MedianFare', 'MaxFare']

y_vars = ['Index of Multiple Deprivation (IMD) Score', 'Income Score (rate)',
'Employment Score (rate)', 'Education, Skills and Training Score',
'Health Deprivation and Disability Score', 'Crime Score',
'Barriers to Housing and Services Score', 'Living Environment Score',
'Income Deprivation Affecting Older People (IDAOPI) Score (rate)',
'Geographical Barriers Sub-domain Score',
'Wider Barriers Sub-domain Score', 'Indoors Sub-domain Score',
'Outdoors Sub-domain Score']

corr = pd.DataFrame()
urban_corr = pd.DataFrame()
rural_corr = pd.DataFrame()

urban_gdf = stn_imd_gdf[stn_imd_gdf['Rural Urban Classification 2011 (2 fold)'] == 'Urban']
rural_gdf = stn_imd_gdf[stn_imd_gdf['Rural Urban Classification 2011 (2 fold)'] == 'Rural']

for x in x_vars:
    
    for y in y_vars:
        
        corr = pd.concat([corr, pd.DataFrame([[x, y, kendall(stn_imd_gdf[x], stn_imd_gdf[y]).correlation, kendall(stn_imd_gdf[x], stn_imd_gdf[y]).pvalue]])]).reset_index(drop = True)
        urban_corr = pd.concat([corr, pd.DataFrame([[x, y, kendall(urban_gdf[x], urban_gdf[y]).correlation, kendall(urban_gdf[x], urban_gdf[y]).pvalue]])]).reset_index(drop = True)
        rural_corr = pd.concat([corr, pd.DataFrame([[x, y, kendall(rural_gdf[x], rural_gdf[y]).correlation, kendall(rural_gdf[x], rural_gdf[y]).pvalue]])]).reset_index(drop = True)

fig, ax = plt.subplots(figsize=(8,8))
im = ax.imshow(corr)
fig.colorbar(im, orientation='vertical')

#the next section can be used to generate the small multiples figure
colors = {'Urban':'tab:cyan', 'Rural':'tab:orange'}
plt.scatter(stn_imd_gdf['MedianFare'], stn_imd_gdf['Index of Multiple Deprivation (IMD) Score'], c = stn_imd_gdf['Rural Urban Classification 2011 (2 fold)'].map(colors), alpha = 0.5)


x_vars = ['Max distance', 
        'Median distance', 'MedianFare', 'MaxFare']

y_vars = ['Index of Multiple Deprivation (IMD) Score', 'Income Score (rate)',
'Employment Score (rate)', 'Education, Skills and Training Score',
'Health Deprivation and Disability Score', 'Crime Score',
'Barriers to Housing and Services Score', 'Living Environment Score',
'Income Deprivation Affecting Older People (IDAOPI) Score (rate)',
'Geographical Barriers Sub-domain Score',
'Wider Barriers Sub-domain Score', 'Indoors Sub-domain Score',
'Outdoors Sub-domain Score']

num = 0

plt.figure(figsize=(50,30), facecolor='white')

for y in y_vars:
    
    for x in x_vars:
        
        num = num + 1
        
        plt.subplot(13, 4, num)
        
        plt.scatter(stn_imd_gdf[x], stn_imd_gdf[y], c = stn_imd_gdf['Rural Urban Classification 2011 (2 fold)'].map(colors), alpha = 0.5)
        plt.xlabel(x)
        plt.ylabel(y)
        # plt.title(x + ' vs ' + y)

plt.tight_layout()
plt.savefig(project_dir + 'small_multiples_IMD_analysis.pdf')


