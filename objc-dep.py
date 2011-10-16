#!/usr/bin/python

# Nicolas Seriot
# 2011-01-06
# https://github.com/nst/objc_dep/
# http://seriot.ch/blog.php?article=20110124

"""
Input: path of an Objective-C project

Output: import dependancies Graphviz format

Typical usage: $ python objc_dep.py /path/to/project > graph.dot

The .dot file can be opened with Graphviz or OmniGraffle.
"""

import sys
import os
import sets
import re

regex_import = re.compile("#import \"(?P<filename>\S*)\.h")

def filenames_imported_in_file(path):
    imports = set()
    
    for line in open(path):
        results = re.search(regex_import, line)
        if results:
            filename = results.group('filename')
            imports.add(filename)
    
    return imports
    
def add_imports_from_files(d, dir, files):
    
    objc_files = (f for f in files if f.endswith('.h') or f.endswith('.m'))
    
    for f in objc_files:
        base_name = f.split('.')[0]
        
        if base_name not in d:
            d[base_name] = set()
        
        path = os.path.join(dir, f)
        if not os.path.isdir(path):
            imports = filenames_imported_in_file(path)
            d[base_name] = d[base_name].union(imports)
    
    return d

def dependancies_in_dot_format(d):
    l = []
    l.append("digraph G {")
    
    for k, set in d.iteritems():
        if set:
            set.discard(k)
        deps = map(lambda s:'"%s"' % s, set)
        deps = '; '.join(deps)
        l.append("\t\"%s\" -> {%s};" % (k, deps))
    l.append("}\n")
    
    return '\n'.join(l)

def dependancies_in_project(path):
    d = {}
    os.path.walk(path, add_imports_from_files, d)
    return d

def main():
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        print "USAGE: $ python %s PROJECT_PATH" % sys.argv[0]
        exit(0)
    
    d = dependancies_in_project(sys.argv[1])
    s = dependancies_in_dot_format(d)
    print s

if __name__=='__main__':
    main()
