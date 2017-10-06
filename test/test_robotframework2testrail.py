#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Test of mod:`robotframework2testrail` """
import os

import robotframework2testrail

RESULTS = [{
    'id': 'C9876',
    'name': 'Testrail2',
    'status': 'FAIL',
    'comment': '# Robot Framework result: #\n    AssertionError',
    'duration': 420
}, {
    'id': 'C344',
    'name': 'Testrail',
    'status': 'PASS',
    'comment': None,
    'duration': 3601,
}, {
    'id': 'C1111',
    'name': 'Testrail3',
    'status': 'PASS',
    'comment': '# Robot Framework result: #\n    Skipped!',
    'duration': 86400
}]


def test_get_testcases():
    """ Test of function `get_testcases` """
    assert robotframework2testrail.get_testcases(
        os.path.join(robotframework2testrail.PATH, 'test', 'output.xml')) == RESULTS
