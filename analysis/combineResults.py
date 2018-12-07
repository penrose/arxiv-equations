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
    "figure_papers": 0,
    "figures": 0,
    "figures_per_page": 0
}

counts_template = global_counts.copy()
topic_counts = dict()

for input_pkl in input_pkls:
    print('Parsing %s' %input_pkl)
    df = pickle.load(open(input_pkl, 'rb'))
    for row in df.iterrows():
        uid = row[0]

        # Skip page counts of none
        if row[1].numberPages == None:
            continue

        # Update global counts
        global_counts['papers'] += 1
        global_counts['files'] += row[1].numberFiles

        # A figure paper has one or more figures
        if row[1].numberFigures > 0:
            global_counts['figure_papers'] += 1

        global_counts['figures'] += row[1].numberFigures
        global_counts['pages'] += row[1].numberPages

        # Update topic conunts (redundant, I know)
        topic = row[1].topic
        if topic not in topic_counts:
            topic_counts[topic] = counts_template.copy()
        topic_counts[topic]['papers'] += 1
        topic_counts[topic]['files'] += row[1].numberFiles

        # A figure paper has one or more figures
        if row[1].numberFigures > 0:
            topic_counts[topic]['figure_papers'] += 1

        topic_counts[topic]['figures'] += row[1].numberFigures
        topic_counts[topic]['pages'] += row[1].numberPages


# Now calculate average figures per page
for topic, values in topic_counts.items():
    values['figures_per_page'] = values['figures'] / values['pages']
    topic_counts[topic] = values

global_counts['figures_per_page'] = global_counts['figures'] / global_counts['pages']
results = {'global': global_counts,
           'topic': topic_counts }
pickle.dump(results, open('arxiv-count-results.pkl','wb'))
