# Cost of train journeys

To install this package, download this repository and run the following from the root directory of the repo:

```bash
# # If you have not previously installed poetry before...
# type the following for osx/linux/bashonwindows:
# curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
# or type the following if you're on Windows:
# (Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -
# See https://python-poetry.org/docs/ for details on installation
poetry install
```

To open a Python session with all the dependencies you can run the following:

```bash
poetry shell
poetry run python
# From the Python shell, load the package to test it's installed:
import railfares.data_parsing as data_parsing

You can get the stations reachable with the specified budget from the specified starting station by running the following code:

```import railfares.data_parsing as data_parsing

project_dir = ''

starting_station = 'newcastle'

budget = 10

df = data_parsing.get_isocost_stations(starting_station, budget, project_dir)
```

```project_dir``` must contain the path to the data (the data is currently not stored on the repo).

You can also try the interactive flask dashboard by running ```flask run``` from the dashboard folder. As above, you need to set the path to where the data is stored in the ```app.py``` file variable ```project_dir```.

# Tutorial
Work in progress..
