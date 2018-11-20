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
    get_recent_builds_URL = CI_API_URL_PREFIX + "/{github_org}/{repo}{branch}?circle-token={ci_token}&limit=100&offset={offset_counter}&filter={filter}"
    get_build_details_URL = CI_API_URL_PREFIX + "/{github_org}/{repo}/{build_num}?circle-token={ci_token}"
    get_test_data_URL = CI_API_URL_PREFIX + "/{github_org}/{repo}/{build_num}/tests?circle-token={ci_token}"

    def __init__(self):
        self.test_times_by_class = {}
        self.median_time_by_class = {}
        self.REPO = sys.argv[1]
        self.branch = ""
        self.filter = "completed"
        self.allowed_test_statuses = ["success", "failure"]
        self.processed_builds = []
        self.test_results = []

        if len(sys.argv) > 2:
            self.build_iterations = int(sys.argv[2])/100
        else:
            self.build_iterations = 1

        if len(sys.argv) > 3:
            self.branch = "/tree/" + sys.argv[3]

        if len(sys.argv) > 4:
            self.mode = sys.argv[4]
            if self.mode == "build_failures":
                self.filter = "failed"
            elif self.mode == "test_failures":
                self.filter = "failed"
                self.allowed_test_statuses = ["failure"]
            else:
                raise Exception(self.mode + " is not an understood argument")

    def _get_recent_builds_for_project(self):
        """
        Get the most recent CI builds for a project as JSON dict
        :return: Dict recent_builds
        """
        recent_builds = []

        for offset_counter in range(0, self.build_iterations):

            print "Getting build " + str(offset_counter*100+1) + " of " + str(self.build_iterations*100)

            recents_url = AnalyzeBuilds.get_recent_builds_URL.format(
                github_org = self.GITHUB_ORG,
                repo = self.REPO,
                branch = self.branch,
                ci_token = self.CI_TOKEN,
                offset_counter = offset_counter*100,
                filter = self.filter
            )

            recent_builds = self._make_json_request(recents_url)
 
            self._process_build_data(recent_builds)

        self.write_csv_file("build.csv", self.processed_builds, ["start_time", "status", "build_time", "failure_step"])
        self.write_csv_file("tests.csv", self.test_results,["build", "test_class", "test_name","full_name", "result", "run_time", "message"])

        return recent_builds

    def _process_build_data(self, builds):

        for build in builds:

            failure_step = ""
            if self.filter == 'failed':
                failure_step = self._get_failure_reason(build)

            build_datetime_utc = dateutil.parser.parse(build["start_time"])
            eastern = timezone('US/Eastern')
            build_time_string =  build_datetime_utc.astimezone(eastern).strftime('%Y-%m-%d %H:%M:%S')

            self._get_test_results(build)

            self.processed_builds.append({
                "start_time": build_time_string, 
                "status": build["status"], 
                "build_time": build["build_time_millis"], 
                "failure_step": failure_step
            })        

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

    def _get_test_results(self, build):

        test_url = AnalyzeBuilds.get_test_data_URL.format(
            github_org=self.GITHUB_ORG,
            repo=self.REPO,
            ci_token=self.CI_TOKEN,
            build_num=build["build_num"]
        )

        test_data = self._make_json_request(test_url)

        for test in test_data["tests"]:

            if test["result"] in self.allowed_test_statuses :
                self.test_results.append({
                    "build": build["build_num"],
                    "test_class": test["classname"],
                    "test_name": test["name"],
                    "full_name": test["classname"] + "." + test["name"],
                    "result": test["result"],
                    "run_time": test["run_time"],
                    "message": test["message"]
                })

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
    def write_csv_file(csv_output_filename, csv_data, field_names):

        with open(csv_output_filename, 'w') as csvfile:
            csv_writer = csv.DictWriter(
                csvfile,
                fieldnames=field_names,
                delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writeheader()
            for row in csv_data:
                csv_writer.writerow(row)


if __name__ == '__main__':
    create_test_suites = AnalyzeBuilds()
    create_test_suites._get_recent_builds_for_project()
