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
import tarfile
import tempfile
import PyPDF2 
from helpers import ( 
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


def extract_paper(tar, member):
    
    # This second tar is a folder with one paper
    subtar = tarfile.open(mode='r|gz', fileobj=tar.extractfile(member))

    # Each submember can be a paper
    texs = []
    for submember in subtar:
        if submember.name.endswith('tex'):
            with subtar.extractfile(submember) as m:
                raw = m.read()
                try:
                    raw = raw.decode('utf-8')
                except:
                    pass
                texs.append(raw)

    # Extract latex
    if len(texs) == 0:
        return None

    try:
        tex = ''.join(texs)
    except:
        tex = ''.join(['%r' %t for t in texs])

    # Unique identifier
    uid = get_uid(member.name)
    year = os.path.basename(uid)[0:2]
    month = os.path.basename(uid)[2:4]

    # Count number of pages
    try:
        number_pages = getNumberPages(uid, tmpdir)
    except: # can't find EOF and can't read PDF errors
        number_pages = 0

    # Count number of figures
    numberFigures = countFigures(tex)

    # If it's zero, check for macros
    if numberFigures == 0:
        numberFigures = countFigures(tex, regexp='\\def\\figure')

    # Count number of lines
    numberLines = len(tex.split('\\n'))
    if numberLines == 1:
        numberLines = len(tex.split('\n'))

    # Metadata file (can regenerate with get_metadata), created with arxiv-equations
    meta_dir = os.path.join(meta_folder, year, month)
    if not os.path.exists(meta_dir):
        os.makedirs(meta_dir)
 
    # Extract metadata using arxiv API, save for later use
    metadata = get_metadata(uid)

    # Save the metadata if we don't have it yet
    meta_file = os.path.join(meta_dir, "extracted_%s.pkl" % uid)
    if not os.path.exists(meta_file):
        pickle.dump(metadata, open(meta_file, 'wb'))
    
    try:
        topic = metadata['arxiv_primary_category']['term']
    except:
        topic = None

    # Try to get tags from API metadata, fall back to None
    try:
        tags = ','.join([x['term'] for x in metadata['tags']])
    except:
        tags = None
    
    # Return dictionary of results
    results = { 
        "numberFiles": len(texs),
        "uid": uid,
        "folder": os.path.dirname(member.name),
        "year": year,
        "month": month,
        "topic": topic,
        "tags": tags,
        "tarfile": tar.name,
        "inputFile": member.name, 
        "numberFiles": len(texs),
        'numberPages': number_pages, 
        'numberLines': numberLines,
        'numberChars': len(tex),
        'numberFigures': numberFigures
    }
    return results
