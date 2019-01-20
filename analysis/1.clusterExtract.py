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
uid = sys.argv[3]

# Full path of file (.tar) to work with
input_tar = os.path.abspath(input_tar)

# Temporary folder for work
tmpdir = tempfile.mkdtemp()

# Ensure that exists
if not os.path.exists(input_tar):
    print('Cannot find %s, exiting!' % input_tar)
    sys.exit(1)

# Read in the tar
# '/scratch/users/vsochat/DATA/arxiv/1306.tar'
tar = tarfile.open(input_tar, 'r')

# And each .tar.gz member
for member in tar:
    if member.isfile():

        # <TarInfo '1306/1306.3882.tar.gz' at 0x7fb747558e58>
        this_uid = get_uid(member.name)

        # Each job only processes one
        if this_uid != uid:
            continue

        # Return lookup dictionary of fields for data frame
        result = extract_paper(tar, member)
        '''
                {'folder': '1306',
                 'inputFile': '1306/1306.5867.tar.gz',
                 'metadata': {}...
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
            result = {'uid': uid,
                      'status': "no latex found"}

        # Create metadata folder
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        pickle.dump(result, open(output_file, 'wb'))

    else:
        print('Skipping %s, not tar.gz' % member.name)
        result = {'uid': member.name,
                  'status': "member is not file"}
        pickle.dump(result, open(output_file, 'wb'))

tar.close()
