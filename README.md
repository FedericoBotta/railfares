# Cost of train journeys

You can get the stations reachable with the specified budget from the specified starting station by running the following code:

```import railfares.data_parsing as data_parsing

project_dir = ''

starting_station = 'newcastle'

budget = 10

df = data_parsing.get_isocost_stations(starting_station, budget, project_dir)
```

```project_dir``` must contain the path to the data (the data is currently not stored on the repo.

You can also try the interactive flask dashboard by running ```flask run``` from the dashboard folder. As above, you need to set the path to where the data is stored in the ```app.py``` file variable ```project_dir```.
