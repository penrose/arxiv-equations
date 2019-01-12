#!/usr/bin/env python
#
# clusterExtract
# This is a modified script (from Dor) to extract metrics for an archive. We
# need to have full paths of the subjects and number of pages files, which
# are included in the repository:
#
#     git clone https://www.github.com/penrose/arxiv-miner
#     cd arxiv-miner
#         src/abscat.csv  # categories / topics
#         src/npages.csv  # number of pages
#
# This script is located under analysis, and expected to be run with the run*
# equivalent. We also expect this to be the present working directory, to 
# import from helpers.py (this is handled in the run_* script)
#
#         analysis/1.run_clusterExtract.py
#         analysis/1.clusterExtract.py

import json
import os
import re
import sys
import pandas
import pickle
import tarfile
import tempfile
import PyPDF2 
from helpers import ( 
    extract_paper,
    find_equations,
    getNumberPages,
    getOrNone,
    get_uid,
    get_metadata,
    recursive_find,
    countFigures 
)


input_tar = sys.argv[1]
output_file = sys.argv[2]
meta_folder = sys.argv[3]

# Full path of file (.tar) to work with
input_tar = os.path.abspath(input_tar)

# Temporary folder for work
tmpdir = tempfile.mkdtemp()

# Ensure that exists
if not os.path.exists(input_tar):
    print('Cannot find %s, exiting!' % input_tar)
    sys.exit(1)


# Create a data frame to hold all input files, parse through .tar.gz found

columns = ['uid',                     # 1306.2580
           'topic',                   # math.RT
           'month',                   # 06
           'year',                    # 13
           'tags',                    # 'math.RT,math.AG'
           'folder',                  # 1306
           'tarfile',                 # '/scratch/users/vsochat/DATA/arxiv/1306.tar'
           'inputFile',               # '1306/1306.5867.tar.gz'
           'numberPages',             # 14 
           'numberLines',             # 124
           'numberChars',             # 59385
           'numberFiles',             # 1
           'numberFigures']           # 0


df = pandas.DataFrame(columns=columns)
rows = []

# Read in the tar
# '/scratch/users/vsochat/DATA/arxiv/1306.tar'
tar = tarfile.open(input_tar, 'r')

# Missing tex files
missing = []

# And each .tar.gz member
for member in tar:
    if member.isfile():

        # <TarInfo '1306/1306.3882.tar.gz' at 0x7fb747558e58>
        uid = get_uid(member.name)

        # Return lookup dictionary of fields for data frame
        result = extract_paper(tar, member)
        '''
                {'folder': '1306',
                 'inputFile': '1306/1306.5867.tar.gz',
                 'month': '06',
                 'numberChars': 59385,
                 'numberFigures': 0,
                 'numberFiles': 1,
                 'numberLines': 124,
                 'numberPages': 14,
                 'tags': 'math.RT,math.AG',
                 'tarfile': '/scratch/users/vsochat/DATA/arxiv/1306.tar',
                 'topic': 'math.RT',
                 'uid': '1306.5867',
                 'year': '13'}
        '''
        if result == None:
            missing_name = "%s|%s" %(tar.name, member.name)
            missing.append(missing_name)
            print("No LaTeX found in %s" % missing_name)
        else:
            row = [ uid,
                    result['topic'],
                    result['month'],
                    result['year'],
                    result['tags'],
                    result['folder'],
                    result['tarfile'],
                    result['inputFile'], 
                    result['numberPages'], 
                    result['numberLines'],
                    result['numberChars'],
                    result['numberFiles'],
                    result['numberFigures']]
            rows.append(row)
    else:
        print('Skipping %s, not tar.gz' % member.name)

# Turn into data frame
dfx = pandas.DataFrame(rows)
dfx.columns = columns
dfx.index = dfx.uid

# Which ones are missing?
missing = []
total = 0
for member in tar:
    if member.isfile():
        uid = get_uid(member.name)
        total += 1
        if uid not in dfx.index.tolist():
            missing.append(uid)

# Save to pickle
pickle.dump(dfx, open(output_file, 'wb'))
dfx.to_csv(output_file.replace('.pkl','.tsv'), sep='\t')
with open(output_file.replace('.pkl','_missing.txt'), 'w') as filey:
    filey.writelines(missing)
