#!/usr/bin/env python3

# MIT license: https://en.wikipedia.org/wiki/MIT_License,

# Copyright (c) 2019, Paul Hammant
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import os
import sys
import sh
import time
from shutil import copyfile
from dateutil.parser import parse
import yaml

def jdefault(o):
    return o.__dict__


def calcStatsForCommit(commit):
    lineCount = 0
    tastableLineCount = 0
    testLineCount = 0

    for chgNum, chunk in enumerate(commit["chunks"], start=1):
        testable = False
        istest = False
        for testable_file_suffix in cfg['testable-file-suffixes']:
            if chunk["from"].endswith(testable_file_suffix) or chunk["to"].endswith(testable_file_suffix):
                testable = True
        if '/test' in chunk["from"] or '/test' in chunk["to"] \
                or 'test/' in chunk["from"] or 'test/' in chunk["to"] \
                or '.Test' in chunk["from"] or '.Test' in chunk["to"] \
                or 'tests/' in chunk["from"] or 'tests/' in chunk["to"]:
            istest = True
        addDelLineCount = 0
        for line in chunk["lines"]:
            if line.startswith("+") or line.startswith("-"):
                addDelLineCount += 1
        lineCount += addDelLineCount
        if testable:
            tastableLineCount += addDelLineCount
            if istest:
                testLineCount += addDelLineCount

    isoformat = commit['when'].isoformat()
    postStats(year + "/" + month + "/" + day, lineCount, testLineCount, tastableLineCount, revHash, commit['who'], isoformat)
    postStats(year + "/" + month, lineCount, testLineCount, tastableLineCount, revHash, commit['who'], isoformat)
    postStats(year, lineCount, testLineCount, tastableLineCount, revHash, commit['who'], isoformat)

    if testLineCount > 0:
        if year not in years:
            years.append(year)
            yearMonths[year] = []
            yearMonthDays[year] = {}
        if month not in yearMonths[year]:
            yearMonths[year].append(month)
            yearMonthDays[year][month] = []
        if day not in yearMonthDays[year][month]:
            yearMonthDays[year][month].append(day)


def postStats(d, lineCount, testLineCount, tastableLineCount, revHash, who, when):
    if not tastableLineCount == 0:
        pct = round(testLineCount * 100 / tastableLineCount, 1)
    else:
        pct = 0.0
    if d not in stats:
        stats[d] = {"commits": [], "description": cfg['description'], "baseURL": cfg["base-diff-url"]}
    stats[d]["commits"].append(
        {"id": revHash, "who": who, "when": when, "all": lineCount, "test": testLineCount, "testable": tastableLineCount, "pct": pct})


def nextDiff(ix, diff):
    try:
        return diff.index("\ndiff --git ", ix)
    except ValueError:
        return len(diff)


def parseChunks():

    ix = diff.index("\nAuthor", 0)
    ix2 = diff.index("\n", ix+1)
    ix_ = diff[ix + 8: ix2]
    commit['who'] = ix_.strip()

    simplifyCommiterID()

    ix = diff.index("\nDate", 0)
    ix2 = diff.index("\n", ix+1)
    commit['when'] = parse(diff[ix + 6: ix2].strip())

    ix = ix2 + 1
    try:
        ix2 = diff.index("\ndiff --git ", ix)
    except ValueError:
        ix2 = len(diff)

    commit['msg'] = diff[ix: ix2].strip()

    while ix2 + 1 < len(diff):
        chunk = {}
        try:
            ix = diff.index("\n---", ix2)
        except ValueError:
            ix2 = nextDiff(ix2 + 1, diff)
            continue
        ix2 = diff.index("\n", ix + 1)
        chunk["from"] = diff[ix + 5:ix2].strip()
        ix = diff.index("\n+++", ix2)
        ix2 = diff.index("\n", ix + 1)
        chunk["to"] = diff[ix + 5:ix2].strip()
        ix2 = nextDiff(ix2 + 1, diff)
        chunk["lines"] = diff[ix + 1:ix2].strip().split("\n")
        commit['chunks'].append(chunk)


def simplifyCommiterID():
    for redaction in cfg['redactions']:
        commit['who'] = commit['who'].replace(redaction, "")
    if ' <' in commit['who']:
        beforeEmail = commit['who'].split(" <")[0]
        upperCt = 0
        nameParts = beforeEmail.split(" ")
        for namePart in nameParts:
            if len(namePart) > 0 and namePart[0].isupper():
                upperCt += 1
        if upperCt > 1:
            commit['who'] = beforeEmail


stats = {}
years = []
yearMonths = {}
yearMonthDays = {}

if len(sys.argv) == 1:
    print("Arg 1 is the path to the repo (a checkout possibly) and dir for the generated metrics.")
    exit(1)

metrics_path = sys.argv[1]
if not metrics_path.endswith("/"):
    metrics_path = metrics_path + "/"

cfg = {}
with open(metrics_path + ".commit-bubbles.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

metrics_data_path = metrics_path + "data/"

if 'write_json_diffs' not in cfg:
    cfg["write_json_diffs"] = False

if 'base-diff-url' not in cfg:
    cfg["base-diff-url"] = "https://github.com/?/?/commit/"

if 'description' not in cfg:
    print("'description' list needed in " + metrics_path + ".commit-bubbles.yml")
    exit(1)

if 'redactions' not in cfg:
    cfg["redactions"] = []

if 'merge-commit-parents' not in cfg:
    cfg["merge-commit-parents"] = False

if 'aliases' not in cfg:
    cfg["aliases"] = []

if 'testable-file-suffixes' not in cfg:
    print("'testable-file-suffixes' list needed in .commit-bubbles.yml")
    exit(1)

copyfile(sys.argv[0].replace("gen-commit-bubbles.py", "index.html"), metrics_path + "index.html")

print("Target directory: " + metrics_path)
print("Initial log...")

if 'source-commits-from-file' not in cfg:
    commits = sh.git("log", "--pretty=format:%H", _tty_out=False)
    commits = commits.split("\n")
else:
    with open(cfg['source-commits-from-file'], 'r') as file:
        commits = file.read().split("\n")

print("Commits to process: " + str(len((commits))))

if cfg['merge-commit-parents']:
    print("looking for missing parents...")
    newCommits = []
    for revHash in commits:
        parents = sh.git("rev-list", "--parents", "-n", "1", revHash, _tty_out=False)
        for parent in parents.strip().split(" "):
            if parent not in commits:
                print("new commit>" + parent + "<")
                newCommits.append(parent)

    print("New commits to process: " + str(len((newCommits))))

    commits.extend(newCommits)

print("Diffs for all commits...")

for revHash in commits:

    commit = {}
    commit['chunks'] = []
    commit["hash"] = revHash

    diff = sh.git("show", revHash, "--no-prefix", _tty_out=False, _encoding="utf-8")
    diff.wait()
    try:
        diff = str(diff)
    except UnicodeDecodeError:
        print("git-show UnicodeDecodeError for " + revHash)
        continue

    parseChunks()

    for alias in cfg['aliases']:
        preferred = alias.split(";")[0]
        terms = alias.split(";")[1].split(",")
        for term in terms:
            if term in commit['who']:
                commit['who'] = preferred

    start = time.time()
    year = str(commit['when'].year)
    month = "%02d" % commit['when'].month
    day = "%02d" % commit['when'].day
    hour = "%02d" % commit['when'].hour
    minute = "%02d" % commit['when'].minute
    second = "%02d" % commit['when'].second
    d = metrics_data_path + year + "/" + month + "/" + day + "/"
    f = d + hour + "-" + minute + "-" + second + "-"
    filepath = f + revHash + ".commit.json"

    # print(json.dumps(commit, indent=2, default=jdefault))

    if not os.path.isdir(d):
        os.makedirs(d)

    calcStatsForCommit(commit)

for statNum, path in enumerate(stats, start=1):
    with open(metrics_data_path + path + "/index.json", 'w') as statFile:
        statFile.writelines(json.dumps(stats[path], indent=2))

with open(metrics_data_path + "years.json", 'w') as yrsFile:
    yrsFile.writelines(json.dumps(sorted(years), indent=2))

for year, months in yearMonths.items():
    with open(metrics_data_path + str(year) + "/months.json", 'w') as monthsFile:
        monthsFile.writelines(json.dumps(sorted(months), indent=2))
    for month in months:
        with open(metrics_data_path + str(year) + "/" + month + "/days.json", 'w') as daysFile:
            daysFile.writelines(json.dumps(sorted(yearMonthDays[year][month]), indent=2))
