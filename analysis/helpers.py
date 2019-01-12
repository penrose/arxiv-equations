import os
import arxiv
import tarfile
import requests
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
    if re.search('[0-9]{4}[.][0-9]+.tar.gz$',os.path.basename(input_file)):
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


def find_equations(tex):
    '''find equations. We assume an equation is either between $$ tags, or
       a begin/end align or equation.'''

    # Extract the equations from the tex
    regexps = [
               r"\$.*?(?<!\\\\)\$",
               r"\\\[.*?(?<!\\\\)\\\]",
               r"\\\(.*?(?<!\\\\)\\\)",
               r"\\begin[{]align[}](.*?(?<!\\\\))\\end[{]align[}]",
               r"\\begin[{]align[*][}](.*?(?<!\\\\))\\end[{]align\*[}]",
               r"\\begin[{]equation[}](.*?(?<!\\\\))\\end[{]equation[}]",
               r"\\begin[{]equation[*][}](.*?(?<!\\\\))\\end[{]equation[*][}]",
               r"\\begin[{]displaymath[}](.*?(?<!\\\\))\\end[{]displaymath[}]",
               r"\\begin[{]displaymath[*][}](.*?(?<!\\\\))\\end[{]displaymath[*][}]",
               r"\\begin[{]eqnarray[}](.*?(?<!\\\\))\\end[{]eqnarray[}]",
               r"\\begin[{]eqnarray[*][}](.*?(?<!\\\\))\\end[{]eqnarray[*][}]",
               r"\\begin[{]multline[}](.*?(?<!\\\\))\\end[{]multline[}]",
               r"\\begin[{]multline[*][}](.*?(?<!\\\\))\\end[{]multline[*][}]",
               r"\\begin[{]gather[}](.*?(?<!\\\\))\\end[{]gather[}]",
               r"\\begin[{]gather[*][}](.*?(?<!\\\\))\\end[{]gather[*][}]",
               r"\\begin[{]falign[}](.*?(?<!\\\\))\\end[{]falign[}]",
               r"\\begin[{]falign[*][}](.*?(?<!\\\\))\\end[{]falign[*][}]",
               r"\\begin[{]alignat[}](.*?(?<!\\\\))\\end[{]alignat[}]",
               r"\\begin[{]alignat[*][}](.*?(?<!\\\\))\\end[{]alignat[*][}]",
    ]
    equations = []
    for regexp in regexps:
        equations = equations + re.findall(regexp, "%r"%str(tex))
    return equations


def extract_inventory(input_file, gzip=False):
    '''extract just the members of a tarfile, meaning we treat each included
       .tar.gz as a paper, and return a list of unique ids to add to our
       data frame

       Parameters
       ==========
       input_file: the .tar folder of .tar.gz (each a paper) from arxiv
       gzip: if the top file to read is gzipped (default is False)
    '''

    fmt = 'r:gz'
    if gzip is False:
        fmt = 'r'
    tar = tarfile.open(input_file, fmt)
    members = []

    # Add each .tar.gz member
    try:
        for member in tar:
            if member.isfile():
                uid = os.path.basename(member.name).replace('.tar.gz', '')
                members.append([input_file, member.name, uid])
            else:
                print('Skipping %s, not tar.gz' % member.name)
    except:
        pass 

    return members


def has_docs(input_file):
    '''count files that end in doc or docx
    '''
    tar = tarfile.open(input_file, "r:gz")

    for member in tar.getmembers():
        if re.search('doc|docx', member.name.lower()):
            return True
    return False    


def getNumberPages(uid, tmpdir):

    npages = 0
    response = requests.get('https://arxiv.org/pdf/%s.pdf' % uid)
    output_pdf = os.path.join(tmpdir, '%s.pdf' % uid)

    if response.status_code == 200:
        with open(output_pdf, 'wb') as filey:
            filey.write(response._content)

    if os.path.exists(output_pdf):
        pdfFile = open(output_pdf, 'rb') 
        pdfReader = PyPDF2.PdfFileReader(pdfFile) 
        npages = pdfReader.numPages
        os.remove(output_pdf)

    return npages


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


def find_folders(base, pattern=None, level=None):
    '''Use os.listdir (as an interator) so we don't stress the file
       system
  
       Parameters
       ==========
       level: if not None, only look this number levels
       base: the root directory to start at
       pattern: a pattern to match
    '''
    if pattern is None:
        pattern = "*"
    start_sep = base.count(os.path.sep)
    for root, dirnames, filenames in os.walk(base):
        number_seps = root.count(os.path.sep) - start_sep
        # We don't want to go any deeper than specified additional levels
        if level != None:
            if number_seps < level:        
                for dirname in dirnames:
                    yield os.path.join(root, dirname)
        # We traverse all levels
        else:
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

    # Extract equations (remove additional escaping, will need to remove /r,/n)
    equations = find_equations(tex) 
    raw =  [e.replace('\\\\','\\') for e in equations]

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
    metadata['equations'] = raw

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
        "equations": raw,
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
