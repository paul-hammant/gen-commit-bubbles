This tech generates a static micro-site that analyzes all the commits for one Git repo/branch for correctness versus some idealized
**"commits should contain test and prod code in a decent proportion"** measure. Python processes the commits (from a local clone), 
and a Vue.JS application shows the analysis in a pretty interactive graph. It does not add the graph for for new commits (pushes), 
it processes all commits that are local. You'd run it daily if you were privately hosting the micro-site.

## To make your own

1. Clone this repo
1. Adjacent to that, clone the repo you want to analyze - lets call that `fred`
1. cd to that clone/checkout dir: `cd fred`
1. Generated bubble data doesn't go that dir, it goes in an adjacent one: `mkdir ../fred-metrics`
1. `cp ../gen-commit-bubbles/.commit-bubble.yml ../fred-metrics/`
1. Edit that and customize: `nano ../fred-metrics/.commit-bubble.yml` remembering that not all source is testable
1. Python3 packages needed: `pip3 install pyyaml sh python-dateutil six`
1. `time python3 ../gen-commit-bubbles/gen-commit-bubbles.py /path/to/fred-metrics/`
1. `cd ../fred-metrics/`
1. Serve current dir over http: `python -m SimpleHTTPServer 8000`
1. open http://localhost:8000 in your fave browser

You can put the generated HTML app online or not - your choice

## Examples of output

I have five example reports online (GitHub Pages), linking to notable years:

1. Java version of Hamcrest (a library for better tests): [commit-bubbles-examples/hamcrestjava/#/2008](https://paul-hammant.github.io/commit-bubbles-examples/hamcrestjava/#/2008)
2. XStream (Java object graph <--> XML): [commit-bubbles-examples/xstream/#/2007](https://paul-hammant.github.io/commit-bubbles-examples/xstream/#/2007)
3. Redis (well known RAM caching tech written in C with TCL tests): [commit-bubbles-examples/redis/#/2019](https://paul-hammant.github.io/commit-bubbles-examples/redis/#/2019)
4. NHibernate-core (.NET object relational mapping framework written in C# ): [commit-bubbles-examples/nhibernate/#/2019](https://paul-hammant.github.io/commit-bubbles-examples/nhibernate/#/2019)
4. Angular (famous TypeScript web framework): [commit-bubbles-examples/angular/](https://paul-hammant.github.io/commit-bubbles-examples/angular)

The Angular charts take 12 mins to generate (python) and have way too much data to be be used for decision making. They will 
also render after a delay (15 seconds of JavaScript in the browser). There's a full circle aspect to that though, and Miško 
Hevery wrote the original "commit bubbles" tech in Flash in Google before going on to write AngularJS in 2009 (see below).

Redis is interesting as its tests are in a different language to the choice of prod code. TCL vs C and a "good" ratio of lines of code may 
be some distance from 50:50. 

### NHibernate 2018 screen-cap

![2019-09-25_0926](https://user-images.githubusercontent.com/82182/65583169-a3473a80-df76-11e9-89ad-48b5227fbc03.png)

## Prior work

* [Improving Developers Enthusiasm For Unit Tests Using Bubble Charts](http://jawspeak.com/2011/07/16/improving-developers-enthusiasm-for-unit-tests-using-bubble-charts/) - Jon Wolter, 2011
* [Angular Commit Bubbles](https://paulhammant.com/2014/10/30/angular-commit-bubbles/) - me, 2014
* [Older VueJS port of the 2014 AngularJS](https://github.com/paul-hammant/gen-commit-bubbles) - me with paid UpWorker help, 2018

## TODO

1. Slow loading - needs a loading interstitial
2. Glitches in UI
3. List of committers (and checkboxes for same) smushed if more than one line
5. Adapt canvas to size of the web page

## Me?

I'm that Trunk-Based Development guy - I visit enterprises and give them a plan to get from bad branching models 
and slow release cadence to Trunk-Based Development and an increased release cadence