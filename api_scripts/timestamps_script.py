import requests
import os
import shutil
from urllib.request import urlopen
from urllib.parse import urlencode
from contextlib import closing
try:
   from PIL import Image
except:
   print("If you are on a Windows machine, please install PIL (imaging library) using 'python -m pip install Pillow' in the Anaconda Prompt")
   exit()
import json


def requestFile(query): 

    # Assemble full request

    # https://navigator.oceansdata.ca/api/v1.0/timestamps/?dataset=giops_day&variable=votemper&_=1622996901202
    base_url = f"http://navigator.oceansdata.ca/api/v1.0/timestamps/?dataset={query['dataset']}&variable={query['variable']}"
    base_url = f"http://navigator.oceansdata.ca/api/v1.0/timestamps/?"
    url = base_url + urlencode({"query": json.dumps(query)})
    print(base_url)

    # Save file and finish
    data_file = requests.get(base_url, stream=True)
    dump = data_file.raw
    # change this if you want a different save location
    location = os.getcwd()
    with open("script_output.csv", "wb") as location:
        print('Saving File')
        shutil.copyfileobj(dump, location)
        print('Done')

    return 1

