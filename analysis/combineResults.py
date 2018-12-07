#!/usr/bin/env python

import os
import pickle
import time
from analysis.helpers import ( recursive_find, here, has_docs )

# git clone https://www.github.com/penrose/arxiv-miner && cd arxiv-miner
# module load python/3.6.1
# module load py-pandas/0.23.0_py36
# module load py-ipython/6.1.0_py36

base = "/regal/users/vsochat/WORK/arxiv-miner"
database = os.path.abspath('counts')

input_pkls = recursive_find(database, '*.pkl')

################################################################################
## Step 1. How many papers missing page counts?
################################################################################

missing = 0
total = 0
for input_pkl in input_pkls:
    df = pickle.load(open(input_pkl, 'rb'))
    for row in df.iterrows():
        if row[1].numberPages == None:
           missing += 1
        total += 1

# missing
# 408603

# total in npages.csv cat src/npages.csv | wc -l
# 1460335

# total papers
# 1328467


################################################################################
## Step 2. How many total papers, and papers that are doc and docx?
################################################################################

# Find our input files
input_files = recursive_find('../arxiv/data', pattern='*.tar.gz')

docs = 0
total_papers = 0
for input_file in input_files:
    if has_docs(input_file):
        docs += 1
    total_papers += 1

# job was cut, need to do another way

# Global Counts
global_counts = {
    "papers": 0,
    "pages": 0,
    "files": 0,
    "lines": 0,
    "chars": 0,
    "figure_papers": 0,
    "figures": 0,
    "figures_per_page": 0
}

# uid                                               quant-ph/0312047
# topic                                                     quant-ph
# month                                                           12
# year                                                            03
# tags                                                      quant-ph
# inputFile        /scratch/users/vsochat/WORK/arxiv/data/quant-p...
# numberPages                                                      8
# numberLines                                                    706
# numberChars                                                  38228
# numberFiles                                                      1
# numberFigures                                                    8

counts_template = global_counts.copy()
topic_counts = dict()
date_counts = dict()

def update_counts(counts, row):

    counts['papers'] += 1
    counts['files'] += row[1].numberFiles

    # A figure paper has one or more figures
    if row[1].numberFigures > 0:
        counts['figure_papers'] += 1
    counts['figures'] += row[1].numberFigures
    counts['lines'] += row[1].numberLines
    counts['chars'] += row[1].numberChars
    counts['pages'] += row[1].numberPages
    return counts

for input_pkl in input_pkls:
    print('Parsing %s' %input_pkl)
    df = pickle.load(open(input_pkl, 'rb'))
    for row in df.iterrows():
        uid = row[0]

        # Skip page counts of none
        if row[1].numberPages == None:
            continue

        # Update global counts
        global_counts = update_counts(global_counts, row)

        # Update topic counts
        topic = row[1].topic
        if topic not in topic_counts:
            topic_counts[topic] = counts_template.copy()
        topic_counts[topic] = update_counts(topic_counts[topic], row)

        # Update monthly counts
        datestr = "%s%s" %(row[1].year, row[1].month)
        if datestr not in date_counts:
            date_counts[datestr] = counts_template.copy()
            date_counts[datestr]['month'] = row[1].month
            date_counts[datestr]['year'] = row[1].year
        date_counts[datestr] = update_counts(date_counts[datestr], row)


# Now calculate average figures per page
for topic, values in topic_counts.items():
    values['figures_per_page'] = values['figures'] / values['pages']
    topic_counts[topic] = values

for datestr, values in date_counts.items():
    values['figures_per_page'] = values['figures'] / values['pages']
    date_counts[datestr] = values

global_counts['figures_per_page'] = global_counts['figures'] / global_counts['pages']
results = {'global': global_counts,
           'topic': topic_counts,
           'dates': date_counts }

pickle.dump(results, open('arxiv-count-results.pkl','wb'))
