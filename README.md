# circle_stats

## Overview

Used to obtain Circle CI stats for running long term build performance analysis.

## Usage

`circle_stats.py <repo> <number_of_builds> <branch> <filter>`
```
repo = github repository name
number_of_builds = number of builds to analyze (increments of 100)
branch (optional) = the branch that you want to query (default: all branches)
filter (optional) = special filter to apply to the query. Options are "build_failures" and "test_failures". "build_failures" will only include failed builds in the results. "test_failures" will only include failed tests in the results.
```
The following environment variables must also be present to run this script
```
GITHUB_ORG = the organization/user that the github repository belongs to
CI_TOKEN = the CircleCI user token used for making CircleCI API calls
```
