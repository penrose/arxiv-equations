#!/usr/bin/env python

import os
import pickle
import time
from analysis.helpers import ( recursive_find, here )

# git clone https://www.github.com/penrose/arxiv-miner && cd arxiv-miner
# module load python/3.6.1
# module load py-pandas/0.23.0_py36
# module load py-ipython/6.1.0_py36

base = "/scratch/users/vsochat/WORK/arxiv-miner"

# Create directories if they don't exist
os.chdir(base)
output = os.path.join(base, 'counts')
for dirname in ['.job', '.out', 'counts']:
    if not os.path.exists(dirname):
        os.mkdir(dirname)

database = os.path.abspath('../../DATA/arxiv')

# Step 1. Find all the top level (topic) folders (N=175)
input_files = recursive_find(database, '*.tar')

def count_queue():
    user = os.environ['USER']
    return int(os.popen('squeue -u %s | wc -l' %user).read().strip('\n'))

# The base of the metadata directory (organized in same way)
meta_folder = os.path.abspath(os.path.join(base, "metadata"))
if not os.path.exists(meta_folder):
    os.mkdir(meta_folder)

# Step 2. Generate jobs, add any that don't get to run to list
jobs = []
job_limit = 1000

for input_file in input_files:
    count = count_queue()
    name = os.path.basename(input_file).replace('.tar','')
    output_file = os.path.join(output, 'counts_%s.pkl' % name)
    file_name = ".job/%s.job" %(name)
    if not os.path.exists(output_file):
        if count < job_limit:
            print("Processing %s" % name)
            with open(file_name, "w") as filey:
                filey.writelines("#!/bin/bash\n")
                filey.writelines("#SBATCH --job-name=%s\n" %name)
                filey.writelines("#SBATCH --output=.out/%s.out\n" %name)
                filey.writelines("#SBATCH --error=.out/%s.err\n" %name)
                filey.writelines("#SBATCH --time=24:00:00 \n")
                filey.writelines("#SBATCH --mem=8000\n")
                filey.writelines('module load python/3.6.1\n')
                filey.writelines('module load py-pandas/0.23.0_py36\n')
                filey.writelines('cd %s\n' % here)
                filey.writelines("python3 1.clusterExtract.py %s %s %s\n" % (input_file, 
                                                                             output_file, 
                                                                             meta_folder))
                filey.writelines("rm %s" % os.path.abspath(file_name))
                filey.writelines("rm .out/%s.out" % name)
                filey.writelines("rm .out/%s.err" % name)
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
