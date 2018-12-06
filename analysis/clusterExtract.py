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
#         analysis/run_clusterExtract.py
#         analysis/clusterExtract.py

import json
import os
import re
import sys
import pandas
import pickle
from helpers import ( 
    extract_tex, 
    getOrNone,
    get_uid,
    recursive_find,
    countFigures 
)


input_dir = sys.argv[1]
output_file = sys.argv[2]
pages_file = sys.argv[3]
topic_file = sys.argv[4]

# Full path of file to work with
input_dir = os.path.abspath(input_dir)

# Ensure that all inputs exist.
for dirname in [pages_file, topic_file, input_dir]:
    if not os.path.exists(dirname):
        print('Cannot find %s, exiting!' % dirname)
        sys.exit(1)

npages = pandas.read_csv(pages_file, index_col=0, header=None, low_memory=False)
topics = pandas.read_csv(topic_file, index_col=0, header=None, low_memory=False)

npages.columns = ['count']
topics.columns = ['topic']

# Create a data frame to hold all input files, parse through .tar.gz found
columns = ['uid', 
           'topic',
           'inputFile', 
           'numberPages', 
           'numberLines',
           'numberFiles',
           'numberFigures']

df = pandas.DataFrame(columns=columns)

# Find our input files
input_files = recursive_find(input_dir, pattern='*.tar.gz')

for input_file in input_files:

    # Extract latex
    results = extract_tex(input_file)
    if len(results) == 0:
        continue

    number_files = len(results)

    # Metadata based on uid from filename
    tex = ''.join(['%r' %t for t in results])
    uid = get_uid(input_file)

    # We count a figure as \begin{figure}
    number_figures = countFigures(tex)

    # If it's zero, check for macros
    if number_figures == 0:
        countFigures(tex, regexp='\\def\\figure')

    topic = getOrNone(topics, uid, 'topic')
    number_pages = getOrNone(npages, uid, 'count')
    number_lines = len(tex.split('\n')) 
    number_chars = len(tex)
    row =[uid, topic, input_file, number_pages, number_lines, number_files, number_figures]
    df.loc[uid] = row

# Save to pickle
pickle.dump(df, open(output_file,'wb'))
df.to_csv(output_file.replace('.pkl','.tsv'), sep='\t')
