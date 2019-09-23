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
    if tastableLineCount > 0 or cfg['write_json_diffs']:
        postStats(year + "/" + month + "/" + day, lineCount, testLineCount, tastableLineCount, revHash, who, when.isoformat())
        postStats(year + "/" + month, lineCount, testLineCount, tastableLineCount, revHash, who, when.isoformat())
        postStats(year, lineCount, testLineCount, tastableLineCount, revHash, who, when.isoformat())
    if cfg['write_json_diffs']:
        pass

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
    global ix, ix2
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


stats = {}
years = []
yearMonths = {}
yearMonthDays = {}

if len(sys.argv) == 1:
    print("Arg 1 is the path to the repo (checkout) for the metrics")
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
    print("'description' list needed in .commit-bubbles.yml")
    exit(1)

if 'redactions' not in cfg:
    cfg["redactions"] = []

if 'testable-file-suffixes' not in cfg:
    print("'testable-file-suffixes' list needed in .commit-bubbles.yml")
    exit(1)

copyfile(sys.argv[0].replace("gen-commit-bubbles.py", "index.html"), metrics_path + "index.html")

commits = sh.git("log", "--pretty=format:%H %ae %ad", "--date=iso-strict", _tty_out=False)

for commitLine in commits.split("\n"):
    parts = commitLine.split(" ")
    revHash = parts.pop(0)
    when = parse(parts.pop(-1))
    who = " ".join(parts)
    for redaction in cfg['redactions']:
        who = who.replace(redaction, "")
    start = time.time()
    year = str(when.year)
    month = "%02d" % when.month
    day = "%02d" % when.day
    hour = "%02d" % when.hour
    minute = "%02d" % when.minute
    second = "%02d" % when.second
    d = metrics_data_path + year + "/" + month + "/" + day + "/"
    f = d + hour + "-" + minute + "-" + second + "-"
    filepath = f + revHash + ".commit.json"
    if (os.path.isfile(filepath)):
        # print("Skip revision: " + str(revHash) + " duration: " + "%.2f" % ((time.time()-start)*1000) + "ms")
        pass
    else:
        diff = sh.git("show", revHash, "--no-prefix", "--first-parent", _tty_out=False, _encoding="iso-8859-1")
        diff.wait()
        diff = str(diff)

        commit = {}
        commit["who"] = who
        commit["when"] = when.isoformat()
        commit["hash"] = revHash
        commit['chunks'] = []

        ix = diff.index("\nDate: ")
        ix = diff.index("\n", ix + 1)

        try:
            ix2 = diff.index("\ndiff --git ")
        except ValueError:
            ix2 = len(diff)

        msg = diff[ix + 1:ix2].strip()
        commit['msg'] = msg

        parseChunks()

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
