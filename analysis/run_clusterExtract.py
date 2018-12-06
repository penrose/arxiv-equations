#!/usr/bin/env python

import os
import pickle
import time
from analysis.helpers import ( find_folders, here )

# git clone https://www.github.com/penrose/arxiv-miner && cd arxiv-miner
# module load python/3.6.1
# module load py-pandas/0.23.0_py36

base = "/regal/users/vsochat/WORK/arxiv-miner"

# Create directories if they don't exist
os.chdir(base)
output = os.path.join(base, 'counts')
for dirname in ['.job', '.out', 'counts']:
    if not os.path.exists(dirname):
        os.mkdir(dirname)

database = os.path.abspath('../arxiv/data')

# Step 1. Find all the top level (topic) folders
input_dirs = find_folders(database)

# Step 2: point to figure counts file
pages_file = os.path.abspath('src/npages.csv')
topic_file = os.path.abspath('src/abscat.csv')

def count_queue():
    user = os.environ['USER']
    return int(os.popen('squeue -u %s | wc -l' %user).read().strip('\n'))

# Step 2. Generate jobs, add any that don't get to run to list
jobs = []
job_limit = 1000

for input_dir in input_dirs:
    count = count_queue()
    name = os.path.basename(input_dir)
    month = name[0:2]
    year = name[2:]
    output_file = os.path.join(output, month, year, 'counts_%s.pkl' % name)
    output_dir = os.path.dirname(output_file)
    file_name = ".job/%s.job" %(name)
    if not os.path.exists(output_file):
        if count < job_limit:
            print("Processing %s" % name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with open(file_name, "w") as filey:
                filey.writelines("#!/bin/bash\n")
                filey.writelines("#SBATCH --job-name=%s\n" %name)
                filey.writelines("#SBATCH --output=.out/%s.out\n" %name)
                filey.writelines("#SBATCH --error=.out/%s.err\n" %name)
                filey.writelines("#SBATCH --time=60:00\n")
                filey.writelines("#SBATCH --mem=2000\n")
                filey.writelines('module load python/3.6.1\n')
                filey.writelines('module load py-pandas/0.23.0_py36\n')
                filey.writelines('cd %s' % here)
                filey.writelines("python3 clusterExtract.py %s %s %s %s\n" % (input_dir, output_file, pages_file, topic_file))
                filey.writelines("rm %s" % os.path.abspath(file_name))
            os.system("sbatch -p owners .job/%s.job" %name)
        else:
            jobs.append(file_name)
            time.sleep(1)

# Submit remaining

while len(jobs) > 0:
    count = count_queue()
    while count < job_limit:
        job = jobs.pop(0)
        os.system("sbatch -p owners %s" % job)
