#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Tool to publish Robot Framework results in TestRail """
import argparse
import configparser
import datetime
import logging
import os
import sys
import time
import xml.etree.ElementTree as etree

from colorama import Fore, Style, init

import testrail
from testrail_utils import TestRailApiUtils

PATH = os.path.abspath(os.path.dirname(__file__))

COMMENT_SIZE_LIMIT = 1000

# Configure the logging
LOG_FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(filename=os.path.join(PATH, 'robotframwork2testrail.log'), format=LOG_FORMAT, level=logging.DEBUG)
CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setLevel(logging.INFO)
CONSOLE_HANDLER.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger().addHandler(CONSOLE_HANDLER)


def get_testcases(xml_robotfwk_output):
    """ Return the list of Testcase ID with status """
    result = []
    for _, elem in etree.iterparse(xml_robotfwk_output):    # pylint: disable=no-member
        if elem.tag == 'suite':
            testcase_id = elem.find('metadata/item[@name="TEST_CASE_ID"]')
            if testcase_id is not None and elem.find('test/status') is not None:
                status = elem.find('test/status').get('status')
                name = elem.get('name')

                # Retrieve comment
                comment = elem.find('test/status').text
                if comment:
                    # Indent text to avoid string formatting by TestRail. Limit size of comment.
                    comment = "# Robot Framework result: #\n    " + comment[:COMMENT_SIZE_LIMIT].replace('\n', '\n    ')
                    comment += '\n...\nLog truncated' if len(str(comment)) > COMMENT_SIZE_LIMIT else ''
                # Retrieve timing
                start_time = elem.find('test/status').get('starttime')
                end_time = elem.find('test/status').get('endtime')
                duration = 0
                if start_time and end_time:
                    td_duration = datetime.datetime.strptime(end_time + '000', '%Y%m%d %H:%M:%S.%f') \
                               - datetime.datetime.strptime(start_time + '000', '%Y%m%d %H:%M:%S.%f')
                    duration = round(td_duration.total_seconds())
                duration = 1 if (duration < 1) else duration    # TestRail API doesn't manage msec (min value=1s)

                result.append({
                    'id': testcase_id.text,
                    'status': status,
                    'name': name,
                    'comment': comment,
                    'duration': duration
                })
            # Memory optimization: see https://www.ibm.com/developerworks/library/x-hiperfparse/index.html
            elem.clear()
    return result


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

            if publish_blocked is False:
                logging.info('Option "Don\'t publish blocked testcases" activated')
                blocked_tests_list = [
                    test.get('case_id') for test in api.get_tests(run_id) if test.get('status_id') == 2
                ]
                logging.info('Blocked testcases excluded: %s', ', '.join(str(elt) for elt in blocked_tests_list))
                testcases = [
                    testcase for testcase in testcases
                    if api.extract_testcase_id(testcase.get('id')) not in blocked_tests_list
                ]

            for testcase in testcases:
                if version:
                    testcase['version'] = version
                try:
                    api.add_result(run_id, testcase)
                    count += 1
                    pretty_print_testcase(testcase)
                    print()
                except testrail.APIError as error:
                    if 'No (active) test found for the run/case combination' not in str(error):
                        pretty_print_testcase(testcase, str(error))
                        print()
                time.sleep(0.5)
            logging.info('%d result(s) published in Test Run #%d.', count, run_id)
        else:
            logging.error('Test Run #%d is is not available', run_id)
            return False

    elif plan_id:
        if api.is_testplan_available(plan_id):
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
