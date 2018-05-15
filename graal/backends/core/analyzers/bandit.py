# -*- coding: utf-8 -*- the Graal backend.
#
# Copyright (C) 2015-2018 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Valerio Cosentino <valcos@bitergia.com>
#

from collections import Counter
import subprocess

from graal.graal import GraalError
from .analyzer import Analyzer


class Bandit(Analyzer):
    """A wrapper for Bandit, a tool designed to find common security issues in Python code.
    To do this Bandit processes each file, builds an AST from it, and runs appropriate plugins against the AST nodes.
    Once Bandit has finished scanning all the files it generates a report.
    """

    version = '0.1.0'

    def analyze(self, **kwargs):
        """Add security issue data using Bandit.

        :param folder_path: folder path
        :param result: dict of the results of the analysis
        """
        folder_path = kwargs['folder_path']

        try:
            msg = subprocess.check_output(['bandit', '-r', folder_path]).decode("utf-8")
        except subprocess.CalledProcessError as e:
            msg = e.output.decode("utf-8")
            if not msg.startswith("Run started:"):
                raise GraalError(cause="Bandit failed at %s, %s" % (folder_path, msg))
        finally:
            subprocess._cleanup()

        vulns = []
        severities = []
        confidences = []
        loc = None
        skipped = None
        descr = None
        severity = None
        confidence = None
        inIssue = False
        inOverview = False
        lines = msg.lower().split('\n')
        for line in lines:
            if line.startswith(">> issue: "):
                descr = line.replace(">> issue: ", "")
                inIssue = True
            elif line.startswith("code scanned:"):
                inOverview = True
            else:
                if inIssue:
                    line = line.strip()
                    if line.startswith("severity:"):
                        tokens = [t.strip(":") for t in line.split(" ")]
                        severity = tokens[1]
                        confidence = tokens[-1]
                        severities.append(severity)
                        confidences.append(confidence)
                    elif line.startswith("location:"):
                        location = line.replace("location: ", "").replace(folder_path, "")
                        line = location.split(":")[-1]
                        file = location.replace(":" + line, "")
                        vuln = {"file": file,
                                "line": line,
                                "severity": severity,
                                "confidence": confidence,
                                "descr": descr}
                        vulns.append(vuln)
                        severity = None
                        confidence = None
                        descr = None
                        inIssue = False
                elif inOverview:
                    if line.startswith("\ttotal lines of code:"):
                        loc = line.split(":")[1].strip()
                        loc = int(loc)
                        break
                else:
                    continue

        result = {'vulns': vulns,
                  'loc_analyzed': loc,
                  'total_issues': len(vulns),
                  'by_severity': self.__create_ranked_dict(severities),
                  'by_confidence': self.__create_ranked_dict(confidences)}

        return result

    @staticmethod
    def __create_ranked_dict(lst):
        output = {
            "undefined": 0,
            "low": 0,
            "medium": 0,
            "high": 0
        }

        if not lst:
            return output

        counted = Counter(lst)
        for k in counted.keys():
            output[k] = counted[k]

        return output
