#!/usr/bin/env python
#
# generateInventory
# Generate an inventory from the NAS .tar.gz files, including the fullpath
# to the locations and the contents inside.
#

import os
import pickle
import pandas
from analysis.helpers import ( recursive_find, here )

# module load python/3.6.1
# module load py-pandas/0.23.0_py36
# module load py-ipython/6.1.0_py36

# files put here with sftp
base = "/scratch/users/vsochat/DATA/arxiv"

# Figure out number of papers in each, we will assume one subfolder
# in a tar is one paper (possibly with multiple papers)
inventory = pandas.DataFrame()

# Find .tar and .tar.gz - this is just "new" data
files = recursive_find(base, '*.tar')
for input_file in files:
    result = extract_inventory(input_file)
    df = pandas.DataFrame(result, columns=['archive', 'subdirectory', 'uid'])
    inventory = inventory.append(df)

# For now, we will ignore the .tar.gz, it seems much bigger (different?)
print(inventory.shape)
# (947943, 3)


inventory.to_csv('arxiv-inventory-newonly.tsv', sep='\t', index=None)
