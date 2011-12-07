#!/usr/bin/python

# Nicolas Seriot
# 2011-01-06 -> 2011-12-07
# https://github.com/nst/objc_dep/

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
from os.path import basename

regex_import = re.compile("#import \"(?P<filename>\S*)\.h")

def gen_filenames_imported_in_file(path):
    for line in open(path):
        results = re.search(regex_import, line)
        if results:
            filename = results.group('filename')
            yield filename

def dependancies_in_dot_format(d, tw_set=None):
    l = []
    l.append("digraph G {")
    l.append("\tnode [shape=box];")
    two_ways = []

    for k, set in d.iteritems():
        if set:
            set.discard(k)
        
        if len(set) == 0:
            l.append("\t\"%s\" -> {};" % (k))            
        
        for k2 in set:
            if (k, k2) in tw_set or (k2, k) in tw_set:
                two_ways.append((k, k2))
            else:
                l.append("\t\"%s\" -> \"%s\";" % (k, k2))
    
    l.append("\t")
    l.append("\tedge [color=blue];")

    for (k, k2) in two_ways:
        l.append("\t\"%s\" -> \"%s\";" % (k, k2))
    
    l.append("}\n")
    return '\n'.join(l)

def dependancies_in_project(path):
    d = {}
    
    for root, dirs, files in os.walk(path):

        objc_files = (f for f in files if f.endswith('.h') or f.endswith('.m') or f.endswith('.pch'))

        for f in objc_files:
            filename = os.path.splitext(f)[0]

            if filename not in d:
                d[filename] = set()
            
            path = os.path.join(root, f)
            
            for imported_filename in gen_filenames_imported_in_file(path):
                d[filename].add(imported_filename)

    return d
    
def two_ways_dependancies(d):

    two_ways = set()

    # d is {'a1':[b1, b2], 'a2':[b1, b3, b4], ...}

    for a, l in d.iteritems():
        for b in l:
            if b in d and a in d[b]:
                if (a, b) in two_ways:
                    continue
                if (b, a) in two_ways:
                    continue
                if a != b:
                    two_ways.add((a, b))
                    
    return two_ways

def main():
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        print "USAGE: $ python %s PROJECT_PATH" % sys.argv[0]
        exit(0)
    
    d = dependancies_in_project(sys.argv[1])
    two_ways = two_ways_dependancies(d)
    s = dependancies_in_dot_format(d, two_ways)
    print s
  
if __name__=='__main__':
    main()
