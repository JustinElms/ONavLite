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


def requestFile(query, output):

    if output == 'CSV':

        # Assemble full request
        base_url = "http://navigator.oceansdata.ca/api/v1.0/plot/?"
        url = base_url + urlencode({"query": json.dumps(query)}) + '&save&format=csv&size=10x7&dpi=144'
        print(url)


        # Save file and finish
        data_file = requests.get(url, stream=True)
        dump = data_file.raw
        # change this if you want a different save location
        location = os.getcwd()

        with open("script_output.csv", "wb") as location:
            print('Saving File')
            shutil.copyfileobj(dump, location)
            print('Done')
    
    elif output == 'PNG':
        dpi = 144

        # Assemble full request
        base_url = "http://navigator.oceansdata.ca/api/v1.0/plot/?"
        url = base_url + urlencode({"query": json.dumps(query)}) + "&dpi=" + str(dpi)
        print(url)


        #Open URL and save response
        with closing(urlopen(url)) as f:
            img = Image.open(f)
            fname = "script_template_" + str(query["dataset"]) + "_" + str(query["variable"]) + ".png"
            print("Saving as " + fname + " and exiting...")
            img.save(fname , "PNG")

