#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Test of module mod:`testrail_utils` """
from unittest.mock import Mock

import pytest

import testrail_utils as tr
from testrail import APIError

TESTRAIL_URL = 'https://example.testrail.net'

TESTCASES = [{
    'id': 'C9876',
    'name': 'Testrail2',
    'status': 'FAIL',
    'comment': 'ERROR!'
}, {
    'id': 'C344',
    'name': 'Testrail',
    'status': 'PASS'
}, {
    'id': 'C1111',
    'name': 'Testrail3',
    'status': 'PASS',
    'version': '1.0.2',
    'duration': 60
}]

TESTPLAN = {
    "id":
    58,
    "is_completed":
    False,
    "entries": [{
        "id": "ce2f3c8f-9899-47b9-a6da-db59a66fb794",
        "name": "Test Run 5/23/2017",
        "runs": [{
            "id": 59,
            "name": "Test Run 1",
            "is_completed": False,
        }]
    }, {
        "id": "084f680c-f87a-402e-92be-d9cc2359b9a7",
        "name": "Test Run 5/23/2017",
        "runs": [{
            "id": 60,
            "name": "Test Run 2",
            "is_completed": True,
        }]
    }, {
        "id": "775740ff-1ba3-4313-a9df-3acd9d5ef967",
        "name": "Test Run 3",
        "runs": [{
            "id": 61,
            "is_completed": False,
        }]
    }]
}


@pytest.fixture
def api():
    """ Return access to TestRail API """
    inst = tr.TestRailApiUtils(TESTRAIL_URL)
    inst.send_get = Mock()
    inst.send_post = Mock()
    return inst


def test_add_result(api):    # pylint: disable=redefined-outer-name
    """ Test of method `add_results` """
    api.add_result(1, TESTCASES[0])
    api.send_post.assert_called_once_with(
        tr.API_ADD_RESULT_CASE_URL.format(run_id=1, case_id=9876), {'status_id': 5,
                                                                    'comment': 'ERROR!'})

    api.add_result(1, TESTCASES[2])
    api.send_post.assert_called_with(
        tr.API_ADD_RESULT_CASE_URL.format(run_id=1, case_id=1111),
        {'status_id': 1,
         'version': '1.0.2',
         'elapsed': '60s'})


def test_is_testrun_available(api):    # pylint: disable=redefined-outer-name
    """ Test of method `is_testrun_available` """
    api.send_get.return_value = {'is_completed': False}
    assert api.is_testrun_available(1) is True

    api.send_get.side_effect = APIError('Test Run not found')
    assert api.is_testrun_available(1) is False

    api.send_get.return_value = {'is_completed': True}
    assert api.is_testrun_available(1) is False


def test_is_testplan_available(api):    # pylint: disable=redefined-outer-name
    """ Test of method `is_testplan_available` """
    api.send_get.return_value = {'is_completed': False}
    assert api.is_testplan_available(10) is True

    api.send_get.side_effect = APIError('Test Plan not found')
    assert api.is_testplan_available(10) is False

    api.send_get.return_value = {'is_completed': True}
    assert api.is_testplan_available(10) is False


def test_get_available_testruns(api):    # pylint: disable=redefined-outer-name
    """ Test of method `get_available_testruns` """
    api.send_get.return_value = TESTPLAN
    assert api.get_available_testruns(100) == [59, 61]


def test_extract_testcase_id(api):    # pylint: disable=redefined-outer-name
    """ Test of method `extract_testcase_id` """
    assert api.extract_testcase_id('C1234') == 1234
    assert api.extract_testcase_id('c1234') == 1234
    assert api.extract_testcase_id('C1234 C9874') == 1234
    assert api.extract_testcase_id('1234') == 1234

    # Error cases
    assert api.extract_testcase_id('') is None
    assert api.extract_testcase_id('test') is None
    assert api.extract_testcase_id('test C1234') is None


def test_get_tests(api):    # pylint: disable=redefined-outer-name
    """ Test of method `extract_testcase_id` """
    run_id = 100
    api.get_tests(testrun_id=run_id)
    print(api.send_get.call_args_list)
    api.send_get.assert_called_once_with(tr.API_GET_TESTS_URL.format(run_id=run_id))
