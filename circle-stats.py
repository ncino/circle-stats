#!/usr/bin/env python

import csv
import json
import logging
import os
import sys
import re
import requests
import xmltodict

import datetime
import pytz
from pytz import timezone
import dateutil.parser

class AnalyzeBuilds(object):

    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARN"))

    GITHUB_ORG = os.environ.get('GITHUB_ORG')
    CI_TOKEN = os.environ.get('CI_TOKEN')
    CI_API_URL_PREFIX = "https://circleci.com/api/v1.1/project/github"
    get_recent_builds_URL = CI_API_URL_PREFIX + "/{github_org}/{repo}?circle-token={ci_token}&limit=100&offset={offset_counter}&filter={filter}"
    get_build_details_URL = CI_API_URL_PREFIX + "/{github_org}/{repo}/{build_num}?circle-token={ci_token}"

    def __init__(self):
        self.test_times_by_class = {}
        self.median_time_by_class = {}
        self.REPO = sys.argv[1]

        if len(sys.argv) > 2:
            self.build_iterations = int(sys.argv[2])/100
        else:
            self.build_iterations = 1

        if len(sys.argv) > 3:
            self.filter = sys.argv[3]
        else:
            self.filter = 'completed'

    def _get_recent_builds_for_project(self):
        """
        Get the most recent CI builds for a project as JSON dict
        :return: Dict recent_builds
        """
        recent_builds = []
        build_stats = []

        for offset_counter in range(0, self.build_iterations):

            recents_url = AnalyzeBuilds.get_recent_builds_URL.format(
                github_org=self.GITHUB_ORG,
                repo=self.REPO,
                ci_token=self.CI_TOKEN,
                offset_counter=offset_counter*100,
                filter=self.filter
            )

            recent_builds = self._make_json_request(recents_url)
 
            self._process_build_data(recent_builds, build_stats)

        self.write_csv_file("build.csv", build_stats)

        return recent_builds

    def _process_build_data(self, builds, processed_builds):

        for build in builds:
            if "workflows" in build:
                job_name = build["workflows"]["job_name"]
                if not job_name.startswith("build-and-test"):
                    continue
            else:
                continue

            failure_step = ""
            if self.filter == 'failed':
                failure_step = self._get_failure_reason(build)

            build_datetime_utc = dateutil.parser.parse(build["start_time"])
            eastern = timezone('US/Eastern')
            build_time_string =  build_datetime_utc.astimezone(eastern).strftime('%Y-%m-%d %H:%M:%S')

            processed_builds.append(
                {"start_time": build_time_string, 
                "status": build["status"], 
                "build_time": build["build_time_millis"], 
                "job_name":job_name, 
                "failure_step": failure_step}
            )        

    def _get_failure_reason(self, build):

        details_url = AnalyzeBuilds.get_build_details_URL.format(
            github_org=self.GITHUB_ORG,
            repo=self.REPO,
            ci_token=self.CI_TOKEN,
            build_num=build["build_num"]
        )

        build_details = self._make_json_request(details_url)

        for step in build_details["steps"]:
            for action in step["actions"]:
                if action["status"] != "success":
                    return step["name"]

    def _make_json_request(self, url):
        logging.info("Making request at URL: %s" % url)
        r = requests.get(url=url)
        if not r.status_code == 200:
            return Exception("Error retrieving from {url}: {resp}".format(
                url=url, 
                resp=r.text)
            )   

        return json.loads(r.text)

    @staticmethod
    def write_csv_file(csv_output_filename, csv_data):

        with open(csv_output_filename, 'w') as csvfile:
            csv_writer = csv.DictWriter(
                csvfile,
                fieldnames=["job_name","start_time", "status", "build_time", "failure_step"],
                delimiter=",", quotechar='"', escapechar='\\', quoting=csv.QUOTE_NONE)
            csv_writer.writeheader()
            for row in csv_data:
                csv_writer.writerow(row)


if __name__ == '__main__':
    create_test_suites = AnalyzeBuilds()
    create_test_suites._get_recent_builds_for_project()
