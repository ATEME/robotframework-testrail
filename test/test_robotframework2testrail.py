#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Test of mod:`robotframework2testrail` """
import os
from unittest.mock import Mock, call

import robotframework2testrail
from testrail_utils import TestRailApiUtils

TESTRAIL_URL = 'https://example.testrail.net'

RESULTS = [{
    'status': 'PASS',
    'id': 'C344',
    'comment': None,
    'name': 'Test Suite With Metadata',
    'duration': 1
}, {
    'status': 'FAIL',
    'id': 'C344',
    'comment': '# Robot Framework result: #\n    \n                        Only With Metadata\n                    ',
    'name': 'Test Suite With Metadata',
    'duration': 60
}, {
    'status': 'PASS',
    'id': 'C345',
    'comment': None,
    'name': 'Test Suite With Metadata And Tag',
    'duration': 1
}, {
    'status': 'PASS',
    'id': 'C366',
    'comment': None,
    'name': 'Test With Id 366 From Tag',
    'duration': 3600
}, {
    'status': 'FAIL',
    'id': 'C347',
    'comment': '# Robot Framework result: #\n    \n                        Only With Tag\n                    ',
    'name': 'Test With Id 347 From Tag',
    'duration': 24 * 3600
}, {
    'status': 'PASS',
    'id': '348',
    'comment': None,
    'name': 'Test With Id 348 From Tag',
    'duration': 1
}]


def test_get_testcases():
    """ Test of function `get_testcases` """
    results = robotframework2testrail.get_testcases(os.path.join(robotframework2testrail.PATH, 'test', 'output.xml'))
    assert results == RESULTS


def test_publish_testrun():
    """ Test of function `publish_results` """
    api = Mock()
    api.get_tests.return_value = [{'case_id': 344}, {'case_id': 345}]    # Other case_ids are missing
    testrun_id = 100
    robotframework2testrail.publish_results(api, RESULTS, run_id=testrun_id, version='1.2.3.4')
    api.is_testrun_available.assert_called_with(testrun_id)
    assert api.add_result.call_args_list[0] == call(testrun_id, RESULTS[0])
    assert api.add_result.call_args_list[1] == call(testrun_id, RESULTS[1])
    assert api.add_result.call_args_list[2] == call(testrun_id, RESULTS[2])
    assert len(api.add_result.call_args_list) == 3    # Other case_ids are missing so not published


def test_publish_testplan():
    """ Test of function `publish_results` """
    api = Mock()
    api.get_tests.return_value = [{
        'case_id': 9876
    }, {
        'case_id': 344
    }, {
        'case_id': 345
    }, {
        'case_id': 366
    }, {
        'case_id': 348
    }]
    api.get_available_testruns.return_value = [101, 102]
    robotframework2testrail.publish_results(api, RESULTS, plan_id=100)
    assert api.add_result.call_args_list[0] == call(101, RESULTS[0])
    assert api.add_result.call_args_list[1] == call(101, RESULTS[1])
    assert api.add_result.call_args_list[2] == call(101, RESULTS[2])
    assert api.add_result.call_args_list[3] == call(101, RESULTS[3])
    assert api.add_result.call_args_list[4] == call(101, RESULTS[5])
    assert api.add_result.call_args_list[5] == call(102, RESULTS[0])
    assert api.add_result.call_args_list[6] == call(102, RESULTS[1])
    assert api.add_result.call_args_list[7] == call(102, RESULTS[2])
    assert api.add_result.call_args_list[8] == call(102, RESULTS[3])
    assert api.add_result.call_args_list[9] == call(102, RESULTS[5])


def test_dont_publish_blocked():
    """ Test when blocked testcases are not published """
    api = Mock()
    testrun_id = 100
    api.get_tests.return_value = [{
        'case_id': 344,
        'status_id': 1
    }, {
        'case_id': 345,
        'status_id': 2
    }, {
        'case_id': 348,
        'status_id': 1
    }]
    api.extract_testcase_id = TestRailApiUtils.extract_testcase_id    # don't mock this method
    robotframework2testrail.publish_results(api, RESULTS, run_id=100, publish_blocked=False)
    assert len(api.add_result.call_args_list) == 3
    assert api.add_result.call_args_list[0] == call(testrun_id, RESULTS[0])
    assert api.add_result.call_args_list[1] == call(testrun_id, RESULTS[1])
    assert api.add_result.call_args_list[2] == call(testrun_id, RESULTS[5])
