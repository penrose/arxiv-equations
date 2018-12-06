# ArXiv Miner Analysis

**under development, currently being tested**

Here we will mine papers from [arxiv](https://arxiv.org/help/bulk_data) to derive the following:

 1. a count of the number of figures
 2. summary statistics and change over time
 3. To develop a visualization (catalog) that can nicely portray how groups of papers map to domains of math / methods, by way of the equations they use (this will be the final result in the [arxiv-catalog](https://www.github.com/vsoch/arxiv-catalog) repository.
 
This work was modified from [vsoch/arxiv-equations](https://www.github.com/vsoch/arxiv-equations) to run
in an HPC environment.

## Development

The original [src](../src) folder includes a subfolder of example datasets that were used 
for @dormaayan original analysis, and also can be used here to develop and test. The
testing steps were done in the script [testExtract.py](testExtract.py).

## Running on the Sherlock Cluster

To run the analysis on the [Sherlock cluster](https://www.sherlock.stanford.edu/) at Stanford, I 
will use the scripts[clusterExtract.py](clusterExtract.py) and [run_clusterExtract.py](run_clusterExtract.py) 
to do this in parallel for all the .tar.gz. As mentioned in the original repository describing the files,
the archives were uploaded to the cluster with scp, and then extracted as follows:

```bash
for tarfile in $(ls *.tar)
    do
       if [ ! -d "${tarfile%.tar}" ]; then
           tar -xf $tarfile
           echo "Extracting $tarfile"
       fi
done
```

Then I cloned the repository with code, and we will work from its root:

```bash
git clone git@github.com:penrose/arxiv-miner.git
cd arxiv-miner
```

Our general strategy will be to do the following:

 - extract summary metrics on a per archive basis
 - check that all runs are completed
 - when finished, combine data into final spreadsheets.

If we find interesting (topic level) statistics, we can use the data to create meaningful
visualizations on the [arxiv catalog](https://vsoch.github.io/arxiv-catalog/). 
 

## Notes about the data

It's redundant to put these, but I think redundancy is better in this case so you (the reader)
have knowledge about the data.

**Some entries are withdrawals**

And this corresponds to no latex. For example,

```
<TarInfo '0801.0528/p-withdraw' at 0x7f4ada4d8cc8>
```
would return `None`, and should thus be skipped. Another common pattern 
was to find a txt file with a note about the paper being withdrawn:

```
'%auto-ignore\r\nThis paper has been withdrawn by the author,\r\ndue a publication.'
```

Another kind of "withdrawl" I found later was identified based on papers with 
only one line!

```

```

**Some LaTex files end in TEX**

And so the function should convert to lowercase before any string checking.

