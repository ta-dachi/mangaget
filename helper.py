import time
import re
from random import randint
import datetime
import os
import json
import glob

def sortAlphanumeric(data):
    data = sorted(data, key=lambda item: (int(item.partition(' ')[0])
                if item[0].isdigit() else float('inf'), item))
    pprint(data)
    return data

def mangabeeUrlify(s):
    s = re.sub(r"[^\w\s-]", '', s) # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"\s+", '+', s)     # Replaces all runs of whitespace with a single +
    return s

def mangahereUrlify(s):
    s = re.sub(r"[^/.\:\w\s-]", '', s) # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"\s+", '_', s)     # Replaces all runs of whitespace with a single _
    return s

def onlyNumbers(s):
    s = re.sub(r'[a-zA-Z\s-]+', '', s) # Remove all characters and whitespace and hyphens.
    # s = re.sub(r'[^\d.]+', '', s) # Remove all characters and whitespace
    return s

def onlyNumbersSplit(s):
    return s.split(' ', 1)[0]

def sizeMegs(bytes):
    return bytes/1000000

def sizeKilo(bytes):
    return bytes/1000

def randomSleep(start, to):
    num = randint(start,to)
    time.sleep(num)
    return num

def timestamp():
    return str(datetime.datetime.fromtimestamp(time.time()).strftime('[%Y-%m-%d %H:%M:%S]'))

def imageFileCount(path):
    img_files = glob.glob(os.path.join(path, '*.jpg'))
    return len(img_files)

def writeToJson(data, directory):
    with open(directory, 'w') as outfile: # This file is used to manage the integrity of the chapter downloaded.
        json.dump(data, outfile)
