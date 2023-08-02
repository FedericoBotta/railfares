import requests
import zipfile
import io
import os
import railfares


url = 'https://github.com/FedericoBotta/railfares/releases/download/v1/Data_to_download.zip'

cdir = os.path.dirname(os.path.abspath(railfares.__file__))

response = requests.get(url)

if response.status_code != 200:
    raise ValueError(f"Failed to download the file. Status code: {response.status_code}")

# Create a BytesIO object from the downloaded content
zip_data = io.BytesIO(response.content)

# Unzip the contents
with zipfile.ZipFile(zip_data, 'r') as zip_ref:
   for item in zip_ref.infolist():
        if not item.filename.startswith('__MACOSX'):
            zip_ref.extract(item, cdir)
    
