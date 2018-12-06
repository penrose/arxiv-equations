import os
import arxiv
import tarfile
import fnmatch
import re

try:
    here = os.path.abspath(os.path.dirname(__file__))
except:
    here = os.getcwd()

# Helper Functions

def get_uid(input_file):
    '''The two "dumps" of arxiv files differ in the unique ids. The old style
       includes a string category, the new style is all numeric. This function
       derives an ID that the API will understand, regardless.

       style 1 (based on numbers) xxxx.xxxx
       style 2 (with string topic) /<topic>/xxxx/xxxxxxx
    '''
    if re.search('[0-9]{4}[.][0-9]{4}.tar.gz$',os.path.basename(input_file)):
        return os.path.basename(input_file).replace('.tar.gz','')

    # The difference is the identifier for the file
    suffix = os.path.basename(input_file).replace('.tar.gz','')
    prefix = input_file.split('/')[-3]
    return '%s/%s' %(prefix, suffix)


def get_metadata(arxiv_uid):
    '''use the arxiv api to extract metadata for a paper based on its unique id.
       You can get one or more ids, either providing the uid as a single string
       or a list of strings. If one uid is given, return a lookup dictionary.
       If more than one, returns a list of those.

       Parameters
       ==========
       arxiv_uid: the unique id in the name of the tar.gz (0801.1234.tar.gz)
    '''
    if not isinstance(arxiv_uid, list):
        arxiv_uid = [arxiv_uid]

    result = arxiv.query(id_list=arxiv_uid)
    if len(result) == 1:
        result = result[0]
    return result

def countFigures(tex, regexp='\\begin{figure}'):
     tex = str(tex)
     commented = tex.count("% "+ regexp) + tex.count("%" + regexp)
     return tex.count(regexp) - commented

# Function to try and return None to handle missing data
def getOrNone(dataFrame, key, colname):
    '''get a key from a pandas DataFrame in a col (colname) or return None
    '''
    try:
        return dataFrame.loc[key][colname]
    except:
        pass


def extract_tex(input_file):
    '''given an input file, a compressed tar.gz, de-compress into memory,
       and return tex content (if found) in the file. Returns None if not found.
 
       Parameters
       ==========
       input_file: full (or relative path) to the .tar.gz with a tex in it
       @returns tex: a full string extraction of the tex
    '''
    tar = tarfile.open(input_file, "r:gz")

    # Find the tex file
    tex = None
    for member in tar.getmembers():
        if member.name.lower().endswith('tex'):
            with tar.extractfile(member) as m:
                tex = m.read()
    try:
        return tex.decode('utf-8')
    except:
        return tex.decode("ISO-8859-1")
    return tex

def read_file(filename, mode="r"):
    with open(filename,mode) as filey:
        content = filey.read()
    return content


def write_file(filename, content, mode="w"):
    with open(filename, mode) as filey:
        if isinstance(content, list):
            for item in content:
                filey.writelines(content)
        else:
            filey.writelines(content)
    return filename


def find_folders(base, pattern=None):
    '''Use os.listdir (as an interator) so we don't stress the file
       system
    '''
    if pattern is None:
        pattern = "*"
    for root, dirnames, filenames in os.walk(base):
        for dirname in dirnames:
            yield os.path.join(root, dirname)



def recursive_find(base, pattern=None):
    '''recursively find files that match a pattern

       Paramters
       =========
       base: the root directory to start the seartch
       pattern: the pattern to search for using fnmatch
    '''
    if pattern is None:
        pattern = "*"

    for root, dirnames, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)
