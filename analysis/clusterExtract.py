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
    get_metadata,
    getNumberPages,
    recursive_find,
    countFigures 
)


input_dir = sys.argv[1]
output_dir = sys.argv[2]
output_file = sys.argv[3]
pages_file = sys.argv[4]
topic_file = sys.argv[5]
meta_folder = sys.argv[6]

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
           'month',
           'year',
           'tags',
           'inputFile', 
           'numberPages', 
           'numberLines',
           'numberChars',
           'numberFiles',
           'numberFigures']

df = pandas.DataFrame(columns=columns)

# Find our input files
input_files = recursive_find(input_dir, pattern='*.tar.gz')

for input_file in input_files:

    uid = get_uid(input_file)
    
    # Derive output file, month, year, from uid
    year = os.path.basename(uid)[0:2]
    month = os.path.basename(uid)[2:4]

    # Full output file includes month and year
    output_file = os.path.join(output_dir, year, month, output_file)

    # Extract latex
    results = extract_tex(input_file)
    if len(results) == 0:
        continue

    number_files = len(results)

    # Metadata based on uid from filename
    tex = ''.join(['%r' %t for t in results])

    # We count a figure as \begin{figure}
    number_figures = countFigures(tex)

    # If it's zero, check for macros
    if number_figures == 0:
        countFigures(tex, regexp='\\def\\figure')

    # Metadata file (can regenerate with get_metadata), created with arxiv-equations
    meta_file = os.path.join(meta_folder, year, month, "extracted_%s.pkl" % uid)

    # This was an error on my part - I used the file name instead of month and year!
    if os.path.exists(meta_file):
        metadata = pickle.load(open(meta_file,'rb'))['metadata']
    else:
        metadata = get_metadata(uid)

    # Try to get topic from API metadata, fall back to csv
    try:
        topic = metadata['arxiv_primary_category']['term']
    except:
        topic = getOrNone(topics, uid, 'topic')

    # Try to get tags from API metadata, fall back to None
    try:
        tags = ','.join([x['term'] for x in metadata['metadata']['tags']])
    except:
        tags = None
    
    number_pages = getOrNone(npages, uid, 'count')

    # Try to extract if we don't have in lookup
    if number_pages in [0, '', None]:

        # Returns original if unable to extract
        number_pages = getNumberPages(metadata, number_pages)
        
    number_lines = len(tex.split('\n'))
    if number_lines == 1:
        number_lines = len(tex.split('\\n'))

    number_chars = len(tex)
    row =[uid, topic, month, year, tags, input_file, number_pages, number_lines, number_chars, number_files, number_figures]
    df.loc[uid] = row

# Save to pickle
pickle.dump(df, open(output_file,'wb'))
df.to_csv(output_file.replace('.pkl','.tsv'), sep='\t')
