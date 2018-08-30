#!/usr/bin/env python

import csv
import json
import logging
import os
import re
import requests
import xmltodict

class AnalyzeBuilds(object):

    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARN"))

    GITHUB_USER = os.environ.get('GITHUB_USER')
    CI_TOKEN = os.environ.get('CI_TOKEN')
    REPO = os.environ.get('REPO')
    CI_API_URL_PREFIX = "https://circleci.com/api/v1.1/project/github"
    get_recent_builds_URL = CI_API_URL_PREFIX + "/{github_user}/{repo}?circle-token={ci_token}&limit=100&offset={offset_counter}&filter=completed"

    def __init__(self):
        self.test_times_by_class = {}
        self.median_time_by_class = {}

    def _get_recent_builds_for_project(self):
        """
        Get the most recent CI builds for a project as JSON dict
        :return: Dict recent_builds
        """
        recent_builds = []
        build_stats = []

        for offset_counter in range(0, 50):

            get_url = AnalyzeBuilds.get_recent_builds_URL.format(
                github_user=self.GITHUB_USER,
                repo=self.REPO,
                ci_token=self.CI_TOKEN,
                offset_counter=offset_counter*100
            )
            logging.info("URL for recent builds: %s" % get_url)
            r = requests.get(url=get_url)
            if not r.status_code == 200:
                return Exception("Error retrieving recent builds for project: %s" % r.text)

            recent_builds = json.loads(r.text)

            for build in recent_builds:
                build_stats.append({"start_time": build["start_time"], "status": build["status"], "build_time": build["build_time_millis"]})        
        

        self.write_csv_file("build.csv", build_stats)

        return recent_builds

    @staticmethod
    def write_csv_file(csv_output_filename, csv_data):

        with open(csv_output_filename, 'w') as csvfile:
            csv_writer = csv.DictWriter(
                csvfile,
                fieldnames=["start_time", "status", "build_time"],
                delimiter=",", quotechar='"', quoting=csv.QUOTE_NONE)
            csv_writer.writeheader()
            for row in csv_data:
                csv_writer.writerow(row)


if __name__ == '__main__':
    create_test_suites = AnalyzeBuilds()
    create_test_suites._get_recent_builds_for_project()
