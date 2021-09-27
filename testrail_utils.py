#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Various useful class using TestRail API """
import logging
import string

import testrail

API_ADD_RESULT_CASE_URL = 'add_result_for_case/{run_id}/{case_id}'
API_ADD_RESULT_CASES_URL = 'add_results_for_cases/{run_id}'
API_GET_RUN_URL = 'get_run/{run_id}'
API_GET_PLAN_URL = 'get_plan/{plan_id}'
API_GET_TESTS_URL = 'get_tests/{run_id}&limit={limit}&offset={offset}'

ROBOTFWK_TO_TESTRAIL_STATUS = {
    "PASS": 1,
    "SKIP": 4,
    "FAIL": 5,
}

class TestRailApiUtils(testrail.APIClient):
    """ Class adding facilities to manipulate Testrail API """

    def add_result(self, testrun_id, testcase_info):
        """ Add a result to the given Test Run

        :param testrun_id: Testrail ID of the Test Run to feed
        :param testcase_info: Dict containing info on testcase

        """
        data = {'status_id': ROBOTFWK_TO_TESTRAIL_STATUS[testcase_info.get('status')]}
        if 'version' in testcase_info:
            data['version'] = testcase_info.get('version')
        if 'comment' in testcase_info:
            data['comment'] = testcase_info.get('comment')
        if 'duration' in testcase_info:
            data['elapsed'] = str(testcase_info.get('duration')) + 's'
        testcase_id = self.extract_testcase_id(testcase_info['id'])
        if not testcase_id:
            logging.error('Testcase ID is bad formatted: "%s"', testcase_info['id'])
            return None

        return self.send_post(API_ADD_RESULT_CASE_URL.format(run_id=testrun_id, case_id=testcase_id), data)

    def add_results(self, testrun_id, version, testcase_infos):
        """ Add a results to the given Test Run

        :param testrun_id: Testrail ID of the Test Run to feed
        :param version: Test version
        :param testcase_infos: List of dict containing info on testcase

        """
        data = []
        for testcase_info in testcase_infos:
            testcase_data = {
                'status_id': ROBOTFWK_TO_TESTRAIL_STATUS[testcase_info.get('status')]
            }
            if version:
                testcase_data['version'] = version
            if 'comment' in testcase_info:
                testcase_data['comment'] = testcase_info.get('comment')
            if 'duration' in testcase_info:
                testcase_data['elapsed'] = str(testcase_info.get('duration')) + 's'
            testcase_id = self.extract_testcase_id(testcase_info['id'])
            if not testcase_id:
                logging.error('Testcase ID is bad formatted: "%s"', testcase_info['id'])
                return None
            testcase_data['case_id'] = testcase_id
            data.append(testcase_data)

        return self.send_post(API_ADD_RESULT_CASES_URL.format(run_id=testrun_id), {'results': data})

    def is_testrun_available(self, testrun_id):
        """ Ask if Test Run is available in TestRail.

        :param testplan_id: Testrail ID of the Test Run
        :return: True if Test Run exists AND is open
        """
        try:
            response = self.send_get(API_GET_RUN_URL.format(run_id=testrun_id))
            return response['is_completed'] is False
        except testrail.APIError as error:
            logging.error(error)
            return False

    def is_testplan_available(self, testplan_id):
        """ Ask if Test Plan is available in TestRail.

        :param testplan_id: Testrail ID of the Test Plan
        :return: True if Test Plan exists AND is open
        """
        try:
            response = self.send_get(API_GET_PLAN_URL.format(plan_id=testplan_id))
            return response['is_completed'] is False
        except testrail.APIError as error:
            logging.error(error)
            return False

    def get_available_testruns(self, testplan_id):
        """ Get the list of available Test Runs contained in a Test Plan

        :param testplan_id: Testrail ID of the Test Plan
        :return: List of available Test Runs associated to a Test Plan in TestRail.
        """
        testruns_list = []
        response = self.send_get(API_GET_PLAN_URL.format(plan_id=testplan_id))
        for entry in response['entries']:
            for run in entry['runs']:
                if not run['is_completed']:
                    testruns_list.append(run['id'])
        return testruns_list

    @staticmethod
    def extract_testcase_id(str_content):
        """ Extract testcase ID (TestRail) from the given string.

            :param str_content: String containing a testcase ID.
            :return: Testcase ID (int). `None` if not found.
        """
        testcase_id = None

        # Manage multiple value but take only the first chunk
        list_content = str_content.split()
        if list_content:
            first_chunk = list_content[0]
            try:
                testcase_id_str = ''.join(char for char in first_chunk if char in string.digits)
                testcase_id = int(testcase_id_str)
            except (TypeError, ValueError) as error:
                logging.error(error)

        return testcase_id

    def get_tests(self, testrun_id, testcase_limit, testcase_offset):
        """ Return the list of tests containing in a Test Run,
            starting at testcase_offset and returning max testcase_limit tests

        :param testrun_id: TestRail ID of the Test Run
        :param testcase_limit: max tests to return for request
        :param testcase_offset: start offset for request

        """
        try:
            return self.send_get(API_GET_TESTS_URL.format(run_id=testrun_id, limit=testcase_limit, offset=testcase_offset))
        except testrail.APIError as error:
            logging.error(error)
