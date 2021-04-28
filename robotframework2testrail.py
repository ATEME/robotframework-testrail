#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Tool to publish Robot Framework results in TestRail """
import argparse
import configparser
import datetime
import logging
import os
import re
import sys
import time

import testrail
from colorama import Fore, Style, init
from robot.api import ExecutionResult, ResultVisitor
from testrail_utils import TestRailApiUtils

# pylint: disable=logging-format-interpolation

PATH = os.getcwd()

COMMENT_SIZE_LIMIT = 1000

# Configure the logging
LOG_FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(filename=os.path.join(PATH, 'robotframework2testrail.log'), format=LOG_FORMAT, level=logging.DEBUG)
CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setLevel(logging.INFO)
CONSOLE_HANDLER.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger().addHandler(CONSOLE_HANDLER)


class TestRailResultVisitor(ResultVisitor):
    """ Implement a `Visitor` that retrieves TestRail ID from Robot Framework Result """

    def __init__(self):
        """ Init """
        self.result_testcase_list = []

    def end_suite(self, suite):
        """ Called when suite end """
        for _suite, test, test_case_id in self._get_test_case_id_from_suite(suite):
            self._append_testrail_result(_suite, test, test_case_id)

    @staticmethod
    def _get_test_case_id_from_suite(suite):
        """ Retrieve list of Test Case ID from a suite
            Manage both case: ID in metadata or in tags.
        """
        testcase_id = 0
        result = []
        # Retrieve test_case_id from metadata
        for metadata in suite.metadata:
            if metadata == 'TEST_CASE_ID':
                testcase_id = suite.metadata['TEST_CASE_ID']
                break    # We only take the first ID found
        # Retrieve test_case_ids from tags
        for test in suite.tests:
            test_case_ids_from_tags = TestRailResultVisitor._get_test_case_ids_from_tags(test.tags)
            if test_case_ids_from_tags:
                for tcid in test_case_ids_from_tags:
                    result.append((test.name, test, tcid))
                    logging.debug("Use TestRail ID from tag: ID = %s", tcid)
            else:
                if testcase_id:
                    result.append((suite.name, test, testcase_id))
                    logging.debug("Use TestRail ID from metadata: ID = %s", testcase_id)
        return result

    @staticmethod
    def _get_test_case_ids_from_tags(tags):
        """ Retrieve all test case tags found in the list """
        test_case_list = []
        for tag in tags:
            if re.findall("(test_case_id=[C]?[0-9]+)", tag):
                test_case_list.append(tag[len('test_case_id='):])
        return test_case_list

    def _append_testrail_result(self, name, test, testcase_id):
        """ Append a result in TestRail format """
        comment = None
        if test.message:
            comment = test.message
            # Indent text to avoid string formatting by TestRail. Limit size of comment.
            comment = "# Robot Framework result: #\n    " + comment[:COMMENT_SIZE_LIMIT].replace('\n', '\n    ')
            comment += '\n...\nLog truncated' if len(str(comment)) > COMMENT_SIZE_LIMIT else ''
        duration = 0
        if test.starttime and test.endtime:
            td_duration = datetime.datetime.strptime(test.endtime + '000', '%Y%m%d %H:%M:%S.%f')\
                        - datetime.datetime.strptime(test.starttime + '000', '%Y%m%d %H:%M:%S.%f')
            duration = round(td_duration.total_seconds())
            duration = 1 if (duration < 1) else duration    # TestRail API doesn't manage msec (min value=1s)
        self.result_testcase_list.append({
            'id': testcase_id,
            'status': test.status,
            'name': name,
            'comment': comment,
            'duration': duration
        })


def get_testcases(xml_robotfwk_output):
    """ Return the list of Testcase ID with status """
    result = ExecutionResult(xml_robotfwk_output, include_keywords=False)
    visitor = TestRailResultVisitor()
    result.visit(visitor)
    return visitor.result_testcase_list


def publish_results(api, testcases, run_id=0, plan_id=0, version='', publish_blocked=True):
    # pylint: disable=too-many-arguments, too-many-branches
    """ Update testcases with provided Test Run or Test Plan

        :param api: Client to TestRail API
        :param testcases: List of testcases with status, returned by `get_testcases`
        :param run_id: TestRail ID of Test Run to update
        :param plan_id: TestRail ID of Test Plan to update
        :param version: Version to indicate in Test Case result
        :param publish_blocked: If False, results of "blocked" Test cases in TestRail are not published
        :return: True if publishing was done. False in case of error.
    """
    if run_id:
        if api.is_testrun_available(run_id):
            count = 0
            logging.info('Publish in Test Run #%d', run_id)
            testcases_in_testrun_list = api.get_tests(run_id)

            # Filter tests present in Test Run
            case_id_in_testrun_list = [str(tc['case_id']) for tc in testcases_in_testrun_list]
            testcases = [
                testcase for testcase in testcases if testcase['id'].replace('C', '') in case_id_in_testrun_list
            ]

            # Filter "blocked" tests
            if publish_blocked is False:
                logging.info('Option "Don\'t publish blocked testcases" activated')
                blocked_tests_list = [
                    test.get('case_id') for test in testcases_in_testrun_list if test.get('status_id') == 2
                ]
                logging.info('Blocked testcases excluded: %s', ', '.join(str(elt) for elt in blocked_tests_list))
                testcases = [
                    testcase for testcase in testcases
                    if api.extract_testcase_id(testcase.get('id')) not in blocked_tests_list
                ]
            try:
                result = api.add_results(run_id, version, testcases)
                logging.info('%d result(s) published in Test Run #%d.', len(result), run_id)
            except testrail.APIError:
                logging.exception('Error while publishing results')
        else:
            logging.error('Test Run #%d is is not available', run_id)
            return False

    elif plan_id:
        if api.is_testplan_available(plan_id):
            logging.info('Publish in Test Plan #%d', plan_id)
            for _run_id in api.get_available_testruns(plan_id):
                publish_results(api, testcases, run_id=_run_id, version=version, publish_blocked=publish_blocked)
        else:
            logging.error('Test Plan #%d is is not available', plan_id)
            return False

    else:
        logging.error("You have to indicate a Test Run or a Test Plan ID")
        print(Fore.LIGHTRED_EX + 'ERROR')
        return False

    return True


def pretty_print(testcases):
    """ Pretty print a list of testcases """
    for testcase in testcases:
        pretty_print_testcase(testcase)
        print(Fore.RESET)


def pretty_print_testcase(testcase, error=''):
    """ Pretty print a testcase """
    if error:
        msg_template = Style.BRIGHT + '{id}' + Style.RESET_ALL + '\t' + \
                       Fore.MAGENTA + '{status}' + Fore.RESET + '\t' + \
                       '{name}\t=> ' + str(error)
    elif testcase['status'] == 'PASS':
        msg_template = Style.BRIGHT + '{id}' + Style.RESET_ALL + '\t' + \
                       Fore.LIGHTGREEN_EX + '{status}' + Fore.RESET + '\t' + \
                       '{name}\t'
    else:
        msg_template = Style.BRIGHT + '{id}' + Style.RESET_ALL + '\t' + \
                       Fore.LIGHTRED_EX + '{status}' + Fore.RESET + '\t' + \
                       '{name}\t'
    print(msg_template.format(**testcase), end=Style.RESET_ALL)


def options():
    """ Manage options """
    parser = argparse.ArgumentParser(prog='robotframework2testrail.py', description=__doc__)
    parser.add_argument(
        'xml_robotfwk_output',
        nargs=1,
        type=argparse.FileType('r', encoding='UTF-8'),
        help='XML output results of Robot Framework')
    parser.add_argument(
        '--tr-config',
        dest='config',
        metavar='CONFIG',
        type=argparse.FileType('r', encoding='UTF-8'),
        required=True,
        help='TestRail configuration file.')
    parser.add_argument(
        '--tr-password', dest='password', metavar='API_KEY', help='API key of TestRail account with write access.')
    parser.add_argument(
        '--tr-version', dest='version', metavar='VERSION', help='Indicate a version in Test Case result.')
    parser.add_argument('--dryrun', action='store_true', help='Run script but don\'t publish results.')
    parser.add_argument(
        '--tr-dont-publish-blocked',
        action='store_true',
        help='Do not publish results of "blocked" testcases in TestRail.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--tr-run-id',
        dest='run_id',
        action='store',
        type=int,
        default=None,
        help='Identifier of Test Run, that appears in TestRail.')
    group.add_argument(
        '--tr-plan-id',
        dest='plan_id',
        action='store',
        type=int,
        default=None,
        help='Identifier of Test Plan, that appears in TestRail.')

    opt = parser.parse_known_args()
    if opt[1]:
        logging.warning('Unknown options: %s', opt[1])
    return opt[0]


if __name__ == '__main__':
    # Global init
    init()    # colorama

    # Manage options
    ARGUMENTS = options()

    TESTCASES = get_testcases(ARGUMENTS.xml_robotfwk_output[0].name)

    if ARGUMENTS.dryrun:
        pretty_print(TESTCASES)
        print(Fore.GREEN + 'OK')
        sys.exit()

    # Init global variables
    CONFIG = configparser.ConfigParser()
    CONFIG.read_file(ARGUMENTS.config)
    URL = CONFIG.get('API', 'url')
    EMAIL = CONFIG.get('API', 'email')
    VERSION = ARGUMENTS.version
    PUBLISH_BLOCKED = not ARGUMENTS.tr_dont_publish_blocked
    if ARGUMENTS.password:
        PASSWORD = ARGUMENTS.password
    else:
        PASSWORD = CONFIG.get('API', 'password')

    logging.debug('Connection info: URL=%s, EMAIL=%s, PASSWORD=%s', URL, EMAIL, len(PASSWORD) * '*')

    # Init API
    API = TestRailApiUtils(URL)
    API.user = EMAIL
    API.password = PASSWORD

    # Main
    if publish_results(
            API,
            TESTCASES,
            run_id=ARGUMENTS.run_id,
            plan_id=ARGUMENTS.plan_id,
            version=VERSION,
            publish_blocked=PUBLISH_BLOCKED):
        print(Fore.GREEN + 'OK' + Fore.RESET)
        sys.exit()
    else:
        print(Fore.LIGHTRED_EX + 'ERROR' + Fore.RESET)
        sys.exit(1)
