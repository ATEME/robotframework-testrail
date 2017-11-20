#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Test of mod:`robotframework2testrail` """
import os
from unittest.mock import Mock, call

import robotframework2testrail
from testrail_utils import TestRailApiUtils

TESTRAIL_URL = 'https://example.testrail.net'

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


def test_publish_testrun():
    """ Test of function `publish_results` """
    api = Mock()
    testrun_id = 100
    robotframework2testrail.publish_results(api, RESULTS, run_id=testrun_id, version='1.2.3.4')
    api.is_testrun_available.assert_called_with(testrun_id)
    assert api.add_result.call_args_list[0] == call(testrun_id, RESULTS[0])
    assert api.add_result.call_args_list[1] == call(testrun_id, RESULTS[1])
    assert api.add_result.call_args_list[2] == call(testrun_id, RESULTS[2])


def test_publish_testplan():
    """ Test of function `publish_results` """
    api = Mock()
    api.get_available_testruns.return_value = [101, 102]
    robotframework2testrail.publish_results(api, RESULTS, plan_id=100)
    assert api.add_result.call_args_list[0] == call(101, RESULTS[0])
    assert api.add_result.call_args_list[1] == call(101, RESULTS[1])
    assert api.add_result.call_args_list[2] == call(101, RESULTS[2])
    assert api.add_result.call_args_list[3] == call(102, RESULTS[0])
    assert api.add_result.call_args_list[4] == call(102, RESULTS[1])
    assert api.add_result.call_args_list[5] == call(102, RESULTS[2])


def test_dont_publish_blocked():
    """ Test when blocked testcases are not published """
    api = Mock()
    testrun_id = 100
    api.get_tests.return_value = [{'case_id': 344, 'status_id': 2}]
    api.extract_testcase_id = TestRailApiUtils.extract_testcase_id    # don't mock this method
    robotframework2testrail.publish_results(api, RESULTS, run_id=100, publish_blocked=False)
    assert len(api.add_result.call_args_list) == 2
    assert api.add_result.call_args_list[0] == call(testrun_id, RESULTS[0])
    assert api.add_result.call_args_list[1] == call(testrun_id, RESULTS[2])
