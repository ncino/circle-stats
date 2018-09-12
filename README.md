# circle_stats

## Overview

Used to obtain Circle CI stats for running long term build performance analysis.

## Usage

`circle_stats.py <repo> <number_of_builds> <filter>`
```
repo = github repository name
number_of_builds = number of builds to analyze (increments of 100)
filter = filter to apply to builds. Options are "completed", "successful", "failed", "running"(default = completed)
```
The following environment variables must also be present to run this script
```
GITHUB_ORG = the organization/user that the github repository belongs to
CI_TOKEN = the CircleCI user token used for making CircleCI API calls
```
