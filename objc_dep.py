#!/usr/bin/python

# Nicolas Seriot
# 2011-01-06 -> 2011-12-16
# https://github.com/nst/objc_dep/

"""
Input: path of an Objective-C project

Output: import dependencies Graphviz format

Typical usage: $ python objc_dep.py /path/to/project [-x regex] [-i subfolder [subfolder ...]] > graph.dot

The .dot file can be opened with Graphviz or OmniGraffle.

- red arrows: .pch imports
- blue arrows: two ways imports
"""

import sys
import os
from sets import Set
import re
from os.path import basename
import argparse

regex_import = re.compile("^#(import|include) \"(?P<filename>\S*)\.h")

def gen_filenames_imported_in_file(path, regex_exclude):
    for line in open(path):
        results = re.search(regex_import, line)
        if results:
            filename = results.group('filename')
            if regex_exclude is not None and regex_exclude.search(filename):
                continue
            yield filename

def dependencies_in_project(path, ext, exclude, ignore):
    d = {}
    
    regex_exclude = None
    if exclude:
        regex_exclude = re.compile(exclude)
    
    for root, dirs, files in os.walk(path):

        if ignore:
            for subfolder in ignore:
                if subfolder in dirs:
                    dirs.remove(subfolder)

        objc_files = (f for f in files if f.endswith(ext))

        for f in objc_files:
            filename = os.path.splitext(f)[0]
            
            if regex_exclude is not None and regex_exclude.search(filename):
                continue

            if filename not in d:
                d[filename] = Set()
            
            path = os.path.join(root, f)
            
            for imported_filename in gen_filenames_imported_in_file(path, regex_exclude):
                if imported_filename != filename and '+' not in imported_filename and '+' not in filename:
                    d[filename].add(imported_filename)

    return d

def dependencies_in_project_with_file_extensions(path, exts, exclude, ignore):

    d = {}
    
    for ext in exts:
        d2 = dependencies_in_project(path, ext, exclude, ignore)
        for (k, v) in d2.iteritems():
            if not k in d:
                d[k] = Set()
            d[k] = d[k].union(v)

    return d

def two_ways_dependencies(d):

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

def untraversed_files(d):

    dead_ends = Set()

    for file_a, file_a_dependencies in d.iteritems():
        for file_b in file_a_dependencies:
            if not file_b in dead_ends and not file_b in d:
                dead_ends.add(file_b)

    return dead_ends

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
        
def dependencies_in_dot_format(path, exclude, ignore):

    d = dependencies_in_project_with_file_extensions(path, ['.h', '.hpp', '.m', '.mm', '.c', '.cc', '.cpp'], exclude, ignore)

    two_ways_set = two_ways_dependencies(d)
    untraversed_set = untraversed_files(d)

    category_list, d = category_files(d)

    pch_set = dependencies_in_project(path, '.pch', exclude, ignore)

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

    for k, deps in d.iteritems():
        if deps:
            deps.discard(k)
        
        if len(deps) == 0:
            l.append("\t\"%s\" -> {};" % (k))
        
        for k2 in deps:
            if not ((k, k2) in two_ways_set or (k2, k) in two_ways_set):
                l.append("\t\"%s\" -> \"%s\";" % (k, k2))

    l.append("\t")
    for (k, v) in pch_set.iteritems():
        l.append("\t\"%s\" [color=red];" % k)
        for x in v:
            l.append("\t\"%s\" -> \"%s\" [color=red];" % (k, x))
    
    l.append("\t")
    l.append("\tedge [color=blue, dir=both];")

    for (k, k2) in two_ways_set:
        l.append("\t\"%s\" -> \"%s\";" % (k, k2))

    for k in untraversed_set:
        l.append("\t\"%s\" [color=gray, style=dashed, fontcolor=gray]" % k)
    
    if category_list:
        l.append("\t")
        l.append("\tedge [color=black];")
        l.append("\tnode [shape=plaintext];")
        l.append("\t\"Categories\" [label=\"%s\"];" % "\\n".join(category_list))

    if ignore:
        l.append("\t")
        l.append("\tnode [shape=box, color=blue];")
        l.append("\t\"Ignored\" [label=\"%s\"];" % "\\n".join(ignore))

    l.append("}\n")
    return '\n'.join(l)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_path", help="path to folder hierarchy containing Objective-C files")
    parser.add_argument("-x", "--exclude", nargs='?', default='' ,help="regular expression of substrings to exclude from module names")
    parser.add_argument("-i", "--ignore", nargs='*', help="list of subfolder names to ignore")
    args= parser.parse_args()

    print dependencies_in_dot_format(args.project_path, args.exclude, args.ignore)
  
if __name__=='__main__':
    main()
