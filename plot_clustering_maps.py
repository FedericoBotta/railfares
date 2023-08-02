data = pd.read_csv(project_dir + 'hospitals_clustered.csv')
test = stations.merge(data, left_on = 'CRS Code', right_on = 'origin_crs')

personal_cmap = matplotlib.colors.ListedColormap(['#D81B60', '#1E88E5', '#FFC107','#004D40'])

f, ax = plt.subplots(1)
ax = test.plot(column = 'kmeans_res.cluster', cmap = personal_cmap, axes = ax)
f.suptitle('Hospital accessibility')
ax.set_axis_off()
plt.savefig(project_dir + 'hospitals_access_map.png', dpi = 300)



data = pd.read_csv(project_dir + 'large_employment_clustered.csv')
test = stations.merge(data, left_on = 'CRS Code', right_on = 'origin_crs')

personal_cmap = matplotlib.colors.ListedColormap(['#D81B60', '#FFC107','#1E88E5','#004D40'])

f, ax = plt.subplots(1)
ax = test.plot(column = 'kmeans_res.cluster', cmap = personal_cmap, axes = ax)
f.suptitle('Large employment LSOAs accessibility')
ax.set_axis_off()
plt.savefig(project_dir + 'large_empl_map.png', dpi = 300)


data = pd.read_csv(project_dir + 'medium_employment_clustered.csv')
test = stations.merge(data, left_on = 'CRS Code', right_on = 'origin_crs')

personal_cmap = matplotlib.colors.ListedColormap(['#004D40', '#FFC107', '#D81B60', '#1E88E5'])

f, ax = plt.subplots(1)
ax = test.plot(column = 'kmeans_res.cluster', cmap = personal_cmap, axes = ax)
f.suptitle('Medium employment LSOAs accessibility')
ax.set_axis_off()
plt.savefig(project_dir + 'medium_empl_map.png', dpi = 300)




