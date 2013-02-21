- 2013-02-21 merged changes from jomnius who [added](https://github.com/nst/objc_dep/pull/4) a parameter to exclude directories names by regex
- 2012-05-11 merged changes from jonreid who [added](https://github.com/nst/objc_dep/pull/3) a parameter to exclude class names by regex
- 2012-01-11 merged changes from jomnius who [added](https://github.com/nst/objc_dep/pull/1) support for C projects and better handling of categories
- read [Object graph dependency analysis](http://samuelgoodwin.tumblr.com/post/18345393597/object-graph-dependency-analysis) by Samuel Goodwin
- see also jominus blog post [Dependency Graph Tool for iOS Projects](http://jomnius.blogspot.com/2012/01/dependency-graph-tool-for-ios-projects.html)
- yet another use case on vigorouscoding.com [Better get it right the first time](http://www.vigorouscoding.com/2011/12/better-get-it-right-the-first-time/)

# Refactoring by graphing class dependencies

### Code design and loose coupling

As developers, we all love clean code, but the fact is that most of the time we're dealing with bad code. It may be recent or legacy code, written by ourselves or by other developers. We can recognize bad code because [code](http://en.wikipedia.org/wiki/Code_smell) [smells](http://www.codinghorror.com/blog/2006/05/code-smells.html). In other words, some heuristics raise questions about code quality. Among thoses we can name dead code, which I already wrote about [here](http://seriot.ch/blog.php?article=20080728) and [here](http://seriot.ch/blog.php?article=20100301), and tight coupling.

Tight coupling describes a system where many components depend on many other components. A tightly coupled code base stinks, the coupling points out that some classes assume too many responsibilities or that a responsability is spread over several classes, rather than having its own class. The opposite, loose coupling, shows a better design which promotes single-responsibility and separation of concerns. Loose coupling makes the code easier to test and maintain.

In Objective-C, reducing coupling generally involves [delegates](http://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/ObjectiveC/Articles/ocProtocols.html) and [notifications](http://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/Notifications/Introduction/introNotifications.html%23//apple_ref/doc/uid/10000043i).

### Graphing class dependencies

So how do we achieve loose coupling in our own code? Well, at first, we need to get a better idea on the current coupling. Let us define class dependency: _class A depends on B iff class A imports class B header_. With such a definition, we can draw a graph of dependencies between classes by considering the Objective-C `#import` directives in each class. We assume here that the files are named according to the classes they contain.

I wrote [objc_dep.py](https://github.com/nst/objc_dep), a Python script which extracts imports from Objective-C source code. The output can then be displayed in [GraphViz](http://www.graphviz.org/) or [OmniGraffle](http://www.omnigroup.com/products/omnigraffle/). You can then see an oriented graph of dependencies between classes. Note that we could also compute metrics on coupling but it's not the point here.

### Sample usage

How do we get from the dependencies graph to a better design? There's no determinist algorithm and it depends on your project. Let us apply the script on [FSWalker](http://code.google.com/p/fswalker/), a small iPhone file browser I wrote a long time ago.

#### 1. Generate the graph

    $ python objc_dep.py /path/to/FSWalker > fswalker.dot

#### 2. Open it in OmniGraffle

At this point, we see classes as nodes and dependencies as directed edges.

<a href="https://github.com/nst/objc_dep/raw/master/pics/fswalker1.png"><img src="https://github.com/nst/objc_dep/raw/master/pics/fswalker1.png" width="600" /></a>

#### 3. Remove categories

We can safely remove Objective-C [categories](http://developer.apple.com/library/mac/#documentation/Cocoa/Conceptual/ObjectiveC/Articles/ocCategories.html) from the graph, since referencing categories from many places is not an issue from a design point of view.

<a href="https://github.com/nst/objc_dep/raw/master/pics/fswalker2.png"><img src="https://github.com/nst/objc_dep/raw/master/pics/fswalker2.png" width="600" /></a>

#### 4. Group related classes

Next, we can move the vertices around, try to group classes with a common reponsability into clusters.

<a href="https://github.com/nst/objc_dep/raw/master/pics/fswalker3.png"><img src="https://github.com/nst/objc_dep/raw/master/pics/fswalker3.png" width="600" /></a>

#### 5. Study strange dependencies

The graph now gives a pretty good overview of the overall code structure. The controllers objects have been colored in pink, the model objects in yellow and the network part in blue. The graph allows to sport strange dependencies and question the code design. We can see at first glance that FSWalkerAppDelegate has too many dependencies. Specifically we consider:

a) unreferenced classes or clusters

This is probably dead code which can be removed.

Ok, there is no unreferenced class here, although you will probably find some in bigger projects. 

b) two-ways references

Maybe one class should not reference another directly, but reference a protocol implemented by the other class instead.

We have two examples of two-ways references here, between HTTPServer and HTTPConnection, and also between RootViewController and FSWalkerAppDelegate. The former is part of [CocoaHTTPServer](http://code.google.com/p/cocoahttpserver/) and is not a design issue in our project. However, the latter is an issue. By looking at the code, we will notice that RootViewController doesn't actually use FSWalkerAppDelegate, the import can thus be safely removed.

c) weird references

Some of the import directives may simply be unnecessary, or reveal design issues.

There is no good reason why FSWalkerAppDelegate would reference FSItem, nor InfoPanelController. Code inspection will reveal that DetailViewController and InfoPanelController should not be referenced by FSWalkerAppDelegate but RootViewController instead. So, here is the final graph. The architecture of FSWalker may still be improved, but you get the idea...

<a href="https://github.com/nst/objc_dep/raw/master/pics/fswalker4.png"><img src="https://github.com/nst/objc_dep/raw/master/pics/fswalker4.png" width="600" /></a>

### Real world usage

Here is the kind of chart you can expect with a 100 classes project.

<a href="https://github.com/nst/objc_dep/raw/master/pics/largerproject.png"><img src="https://github.com/nst/objc_dep/raw/master/pics/largerproject.png" width="600" /></a>

### Possible improvements

The Cocoa framework enforces the [MVC paradigm](http://developer.apple.com/technologies/mac/cocoa.html) which states (to be short) that model objects and graphical objects should be clearly separated by controller objects. The script could probably be improved by drawing classes which depend on Foundation and classes which depend on AppKit/UIKit with different colors.

### Conclusion

I have found [objc_dep.py](https://github.com/nst/objc_dep) to be definitely useful on small projects as well as bigger ones. It helped me in getting a clear view of code base structure. Spotting strange dependencies allowed me to ask good questions which led to design simplifications. Such a tool could even be integrated into Apple development tools.

Interestingly, the last chart is quite close to the mental representation I have of the code architecture. It reminds me a discussion I had 15 years ago with a friend who was a champion chess player who could play several "blind" chess games simultaneous. He explained then that he saw a blury chessboard in his head and could move around the pieces as with a small 3D camera. Focusing on a specific piece would then raise awareness of opportunities and risks - dependencies - for this piece. As a side effect, writing this script made me realize that software engineering is pretty similar to chess in this way.
