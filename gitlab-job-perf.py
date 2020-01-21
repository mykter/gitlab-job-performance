#!/usr/bin/env python3
import datetime
import json
import requests
import os
import urllib
import matplotlib.pyplot as plt
import matplotlib.dates
import numpy as np
import argparse
import pathlib
import re
from collections import defaultdict


def setYDurationTicks(ax):
    _, end = ax.get_ylim()
    if end > 600:
        step = 60
    elif end > 30:
        step = 30
    elif end > 5:
        step = 5
    else:
        step = None
    ax.yaxis.set_ticks(np.arange(0, end, step))


def scatterplot(x_data, y_data, x_label="", y_label="", title=""):
    fig, ax = plt.subplots()

    ax.plot_date(x_data, y_data)

    setYDurationTicks(ax)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    fig.autofmt_xdate()
    myFmt = matplotlib.dates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(myFmt)


def histogram(data, bins, cumulative=False, x_label="", y_label="", title=""):
    _, ax = plt.subplots()
    ax.hist(data, bins=bins, cumulative=cumulative)
    setYDurationTicks(ax)
    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)
    ax.set_title(title)


def overtime(jobs, by, stages):
    def p(jobs,  title):
        scatterplot([job["created_at"] for job in jobs],
                    [job["duration"] for job in jobs], "", "Duration (s)", title)
    plotBy(jobs, by, stages, p)


def distribution(jobs, by, stages):
    def p(jobs, title):
        histogram([job["duration"] for job in jobs],
                  "auto", False, "Duration (s)", "", title)
    plotBy(jobs, by, stages, p)


def plotBy(jobs, by, stages, plotter):
    if by == "none":
        plotter(jobs,  "All jobs")
    elif by == "name":
        for stage, names in stages.items():
            for name in names:
                thesejobs = list(filter(
                    lambda job: job["stage"] == stage and job["name"] == name, jobs))
                if len(thesejobs) > 0:
                    plotter(thesejobs,  stage + ": " + name)
    elif by == "stage":
        for stage in stages:
            thesejobs = list(filter(
                lambda job: job["stage"] == stage, jobs))
            if len(thesejobs) > 0:
                plotter(thesejobs,   stage)


def fetch(base, project):
    token = os.getenv("GITLAB_TOKEN")
    headers = {'PRIVATE-TOKEN': token}

    url = base + "/api/v4/projects/" + \
        urllib.parse.quote(project, safe='') + "/jobs"
    params = {"scope": ["success"], "pagination": "keyset", "per_page": 100}

    jobs = []
    while (url):
        page = requests.get(url, params=params, headers=headers)
        page.raise_for_status()
        jobs += page.json()
        print("Got {} jobs".format(len(jobs)))

        if "next" in page.links:
            url = page.links["next"]["url"]
        else:
            url = None

    return jobs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Visualize Gitlab job performance')
    parser.add_argument('instance',
                        help='The URL to your gitlab instance, e.g. https://gitlab.example.com')
    parser.add_argument('project',
                        help='The project to analyze, e.g. mygroup/proj')
    parser.add_argument('--by', choices=["stage", "name", "none"], default="name",
                        help='What granularity to create plots for. To plot all jobs on one graph, use "none"')
    parser.add_argument('--dist', action="store_true",
                        help='Show a histogram of duration distribution (default is a scatter plot of duration against time)')
    parser.add_argument('--since',
                        help='The earliest date to consider')
    parser.add_argument('--cache',
                        help='A file to write (or use if it exists) the raw API results to')
    parser.add_argument('--raw', type=bool,
                        help='Dump the raw data')
    parser.add_argument('--ignore-over', type=int,
                        help='Ignore jobs that took longer than this many seconds')
    parser.add_argument(
        '--ref', help='Only show jobs for a ref that matches this regexp, e.g. master, or ^123')
    parser.add_argument(
        '--stage', help='Only show jobs from a stage that matches this regexp, e.g. test')
    parser.add_argument(
        '--job', metavar="NAME", help='Only show jobs with a name that matches this regexp, e.g. ^build$, or "linux"')

    args = parser.parse_args()

    if args.cache and pathlib.Path(args.cache).exists():
        with open(args.cache, 'r') as cache:
            jobs = json.load(cache)
    else:
        if not args.cache:
            print(
                "Fetching job statistics. Use --cache=<file>.json to skip this step on future runs.")
        jobs = fetch(args.instance, args.project)

    if args.cache:
        with open(args.cache, 'w') as cache:
            json.dump(jobs, cache)

    stages = defaultdict(set)
    for job in jobs:
        if args.raw:
            print(job["created_at"], job["duration"],
                  job["ref"], job["stage"], job["name"])
        job["created_at"] = matplotlib.dates.datestr2num(job["created_at"])
        stages[job["stage"]].add(job["name"])

    if args.since:
        since = matplotlib.dates.datestr2num(args.since)
        print("Showing jobs since " + matplotlib.dates.num2date(since).isoformat())
    else:
        since = 0

    if args.ignore_over:
        ignore_over = args.ignore_over
    else:
        ignore_over = 1000111

    if args.ref:
        ref = re.compile(args.ref)
    else:
        ref = re.compile(".")

    if args.stage:
        stage = re.compile(args.stage)
    else:
        stage = re.compile(".")

    if args.job:
        name = re.compile(args.job)
    else:
        name = re.compile(".")

    jobs = list(filter(lambda job:
                       job["created_at"] >= since and
                       job["duration"] <= ignore_over and
                       ref.match(job["ref"] or "") and
                       stage.match(job["stage"] or "") and
                       name.match(job["name"]),
                       jobs))

    if args.dist:
        distribution(jobs, args.by, stages)
    else:
        overtime(jobs, args.by, stages)
    plt.show()
