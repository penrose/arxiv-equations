#!/usr/bin/env python

import os
import pickle
import time
import tarfile
import pandas

# git clone https://www.github.com/penrose/arxiv-miner && cd arxiv-miner
# module load python/3.6.1
# module load py-pandas/0.23.0_py36
# module load py-ipython/6.1.0_py36

base = "/scratch/users/vsochat/WORK/arxiv-miner"

# Create directories if they don't exist
os.chdir(base)

from analysis.helpers import ( recursive_find, get_uid )

npages_file = os.path.abspath('src/npages.csv')
npages = pandas.read_csv(npages_file, header=None, low_memory=False)
npages.columns = ['uid', 'page_count']

# This is a folder with all the .tar files, each with a subfolder of .tar.gz inside
database = os.path.abspath('../../DATA/arxiv')

# Step 1. Find all the top level (topic) folders (N=175)
input_files = recursive_find(database, '*.tar')

# Let's keep a list of missing
notpresent = []

total = 0
for input_file in input_files:
    if input_file == "/scratch/users/vsochat/DATA/arxiv/1110.tar"
        break

# Read in each tar
total = 0
for input_file in input_files:

    print('Parsing %s' % input_file)

    # '/scratch/users/vsochat/DATA/arxiv/1306.tar'
    tar = tarfile.open(input_file, 'r')

    for member in tar:

        # Skip over top level folder (e.g., 1306)
        if member.isfile():

            # Keep a total, just for kicks and giggles
            total+=1

            # <TarInfo '1306/1306.3882.tar.gz' at 0x7fb747558e58>
            uid = get_uid(member.name)
            if uid not in npages['uid'].tolist():
                notpresent.append(member.name)
                print("Missing %s" % member.name)
