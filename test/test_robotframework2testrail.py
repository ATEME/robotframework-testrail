#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Test of `robotframework2testrail` """
import os

import pytest
import robotframework2testrail

RESULTS = [{
    'id': 'C9876',
    'name': 'Testrail2',
    'status': 'FAIL'
}, {
    'id': 'C344',
    'name': 'Testrail',
    'status': 'PASS'
}, {
    'id': 'C1111',
    'name': 'Testrail3',
    'status': 'PASS'
}]


def test_get_testcases():
    assert robotframework2testrail.get_testcases(
        os.path.join(robotframework2testrail.PATH, 'test', 'output.xml')) == RESULTS
