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
# equivalent:
#
#         analysis/run_clusterExtract.py
#         analysis/clusterExtract.py

import json
import os
import re
import pandas
from helpers import ( 
    extract_tex, 
    get_metadata, 
    read_number_pages,
    recursive_find,
    count_figures 
)


input_dir = sys.argv[1]
output_file = sys.argv[2]
npages_file = sys.argv[3]
topics_file = sys.argv[4]

# Full path of file to work with
input_dir = os.path.abspath(input_dir)

# Ensure that all inputs exist.
for dirname in [npages_file, topics_file, input_dir]:
    if not os.path.exists(dirna,e):
        print('Cannot find %s, exiting!' % dirname)

npages = pandas.read_csv(npages_file, header=None)
topics = pandas.read_csv(topics_file, header=None)

# Create a data frame to hold all input files, parse through .tar.gz found
columns = ['uid', 
           'category',
           'inputFile', 
           'numberPages', 
           'numberLines',
           'numberFigures']

df = pandas.DataFrame(columns=columns)

# Find our input files
input_files = recursive_find(input_dir, pattern='tar.gz')

for input_file in input_files:

    # Extract latex as a long string
    tex = extract_tex(input_file)
 
    # Metadata based on uid from filename
    uid = os.path.basename(input_file).replace('.tar.gz','')
    metadata = get_metadata(uid)

    # We count a figure as \begin{figure}
    number_figures = countFigures(tex)
    number_pages = read_number_pages(uid)
    number_lines = len(tex.split('\n'))
    number_chars = len(tex)
    category = metadata['arxiv_primary_category']['term']

    row =[uid, category, input_file, number_pages, number_lines, number_figures]
    df.loc[uid] = row

# Save to pickle
pickle.dump(df, open(output_file,'wb'))
df.to_csv(output_file.replace('.pkl','.tsv'), sep='\t')
