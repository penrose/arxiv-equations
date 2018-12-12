# ArXiv Miner Analysis

Here we will mine papers from [arxiv](https://arxiv.org/help/bulk_data) to derive the following:

 1. a count of the number of figures
 2. summary statistics and change over time
 3. To develop a visualization (catalog) that can nicely portray how groups of papers map to domains of math / methods, by way of the equations they use (this will be the final result in the [arxiv-catalog](https://www.github.com/vsoch/arxiv-catalog) repository.
 
This work was modified from [vsoch/arxiv-equations](https://www.github.com/vsoch/arxiv-equations) to run
in an HPC environment.

## Development

The original [src](../src) folder includes a subfolder of example datasets that were used 
for @dormaayan original analysis, and also can be used here to develop and test. A test
extraction (without complete data) was done in [test](../test), and hopefully here @vsoch
can include all data.

## Inventory of files

The files were copied from the NAS in Josh Sunshine's office ultimately to the Sherlock
cluster using sftp. An [inventory](inventory.tsv) is included here, which is a basic listing
of the files. We generate this inventory with [generateInventory.py](generateInventory.py).
The inventory [arxiv-inventory-newonly.tsv](arxiv-inventory-newonly.tsv) is included here.

 > The new archive data (in the arxiv folder on the NAS) has 947,943 subfolders.

We can be sure of having these subfolders, each a .tar.gz, and it remains to be seen if each
one has data inside (or could be empty, for example).

### .tar found corrupt
I will try to transfer these again, but it could be the originals were corrupt:

 - '/scratch/users/vsochat/DATA/arxiv/1508.tar'

**Update** I have re-transferred the file, and I was able to extract (I think most)
of the contents, but the end of the file has a `ReadError` so likely we lost a small
subset.
