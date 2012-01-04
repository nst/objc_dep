#!/usr/bin/python

# Nicolas Seriot
# 2011-01-06 -> 2011-12-16
# https://github.com/nst/objc_dep/

"""
Input: path of an Objective-C project

Output: import dependancies Graphviz format

Typical usage: $ python objc_dep.py /path/to/project > graph.dot

The .dot file can be opened with Graphviz or OmniGraffle.

- red arrows: .pch imports
- blue arrows: two ways imports
"""

import sys
import os
from sets import Set
import re
from os.path import basename

regex_import = re.compile("#(import|include) \"(?P<filename>\S*)\.h")

def gen_filenames_imported_in_file(path):
    for line in open(path):
        results = re.search(regex_import, line)
        if results:
            filename = results.group('filename')
            yield filename

def dependancies_in_project(path, ext):
    d = {}
    
    for root, dirs, files in os.walk(path):

        objc_files = (f for f in files if f.endswith(ext))

        for f in objc_files:
            filename = os.path.splitext(f)[0]

            if filename not in d:
                d[filename] = Set()
            
            path = os.path.join(root, f)
            
            for imported_filename in gen_filenames_imported_in_file(path):
                if imported_filename != filename and '+' not in imported_filename:
                    d[filename].add(imported_filename)

    return d

def dependancies_in_project_with_file_extensions(path, exts):

    d = {}
    
    for ext in exts:
        d2 = dependancies_in_project(path, ext)
        for (k, v) in d2.iteritems():
            if not k in d:
                d[k] = Set()
            d[k] = d[k].union(v)

    return d

def two_ways_dependancies(d):

    two_ways = Set()

    # d is {'a1':[b1, b2], 'a2':[b1, b3, b4], ...}

    for a, l in d.iteritems():
        for b in l:
            if b in d and a in d[b]:
                if (a, b) in two_ways or (b, a) in two_ways:
                    continue
                if a != b:
                    two_ways.add((a, b))
                    
    return two_ways

def category_files(d):
    d2 = {}
    l = []
    
    for k, v in d.iteritems():
        if not v and '+' in k:
            l.append(k)
        else:
            d2[k] = v

    return l, d2

def referenced_classes_from_dict(d):
    d2 = {}

    for k, deps in d.iteritems():
        for x in deps:
            d2.setdefault(x, Set())
            d2[x].add(k)
    
    return d2
    
def print_frequencies_chart(d):
    
    lengths = map(lambda x:len(x), d.itervalues())
    if not lengths: return
    max_length = max(lengths)
    
    for i in range(0, max_length+1):
        s = "%2d | %s\n" % (i, '*'*lengths.count(i))
        sys.stderr.write(s)

    sys.stderr.write("\n")
    
    l = [Set() for i in range(max_length+1)]
    for k, v in d.iteritems():
        l[len(v)].add(k)

    for i in range(0, max_length+1):
        s = "%2d | %s\n" % (i, ", ".join(sorted(list(l[i]))))
        sys.stderr.write(s)
        
def dependancies_in_dot_format(path):

    d = dependancies_in_project_with_file_extensions(path, ['.h', '.hpp', '.m', '.mm', '.c', '.cc', '.cpp'])

    two_ways_set = two_ways_dependancies(d)

    category_list, d = category_files(d)

    pch_set = dependancies_in_project(path, '.pch')

    #
    
    sys.stderr.write("# number of imports\n\n")
    print_frequencies_chart(d)
    
    sys.stderr.write("\n# times the class is imported\n\n")
    d2 = referenced_classes_from_dict(d)    
    print_frequencies_chart(d2)
        
    #

    l = []
    l.append("digraph G {")
    l.append("\tnode [shape=box];")
    two_ways = Set()

    for k, deps in d.iteritems():
        if deps:
            deps.discard(k)
        
        if len(deps) == 0:
            l.append("\t\"%s\" -> {};" % (k))
        
        for k2 in deps:
            if (k, k2) in two_ways_set or (k2, k) in two_ways_set:
                two_ways.add((k, k2))
            else:
                l.append("\t\"%s\" -> \"%s\";" % (k, k2))

    l.append("\t")
    for (k, v) in pch_set.iteritems():
        l.append("\t\"%s\" [color=red];" % k)
        for x in v:
            l.append("\t\"%s\" -> \"%s\" [color=red];" % (k, x))
    
    l.append("\t")
    l.append("\tedge [color=blue];")

    for (k, k2) in two_ways:
        l.append("\t\"%s\" -> \"%s\";" % (k, k2))
    
    if category_list:
        l.append("\t")
        l.append("\tedge [color=black];")
        l.append("\tnode [shape=plaintext];")
        l.append("\t\"Categories\" [label=\"%s\"];" % "\\n".join(category_list))

    l.append("}\n")
    return '\n'.join(l)

def main():
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        print "USAGE: $ python %s PROJECT_PATH" % sys.argv[0]
        exit(0)

    print dependancies_in_dot_format(sys.argv[1])
  
if __name__=='__main__':
    main()
