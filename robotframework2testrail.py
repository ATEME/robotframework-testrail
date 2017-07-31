#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Tool to publish Robot Framework results in TestRail """
import argparse
import configparser
import logging
import os
import sys

from colorama import Fore, init
from colorama import Style
from lxml import etree

import testrail
from testrail_utils import TestRailApiUtils

if 'win' in sys.platform:
    init()

PATH = os.path.abspath(os.path.dirname(__file__))

# Configure the logging
LOG_FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(filename=os.path.join(PATH, 'install.log'), format=LOG_FORMAT, level=logging.DEBUG)
CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setLevel(logging.INFO)
CONSOLE_HANDLER.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger().addHandler(CONSOLE_HANDLER)


def get_testcases(xml_robotfwk_output):
    """ Return the list of Testcase ID with status """
    result = []
    for _, suite in etree.iterparse(xml_robotfwk_output, tag='suite'):
        testcase_id = suite.find('metadata/item[@name="TEST_CASE_ID"]')
        if testcase_id is not None and suite.find('test/status') is not None:
            status = suite.find('test/status').get('status')
            name = suite.get('name')
            result.append({'id': testcase_id.text, 'status': status, 'name': name})
        suite.clear()    # Memory optimization: see https://www.ibm.com/developerworks/library/x-hiperfparse/index.html
    return result


def publish_results(api, testcases, run_id=0, plan_id=0):
    """ Update testcases with provided Testrun or Testplan

        :param api: Client to TestRail API
        :param testcases: List of testcases with status, returned by `get_testcases`
        :param run_id: TestRail ID of testrun to update
        :param plan_id: TestRail ID of testplan to update
        :return: True if publishing was done. False in case of error.
    """
    if run_id:
        if api.is_testrun_available(run_id):
            count = 0
            for testcase in testcases:
                try:
                    api.add_result(run_id, testcase)
                    count += 1
                except testrail.APIError as error:
                    pretty_print_testcase(testcase, str(error))
                    print()
            logging.info('%d result(s) published in Testrun #%d.', count, run_id)
        else:
            logging.error('Testrun #%d is is not available', run_id)
            return False

    elif plan_id:
        if api.is_testplan_available(plan_id):
            for run_id in api.get_available_testruns(plan_id):
                publish_results(api, testcases, run_id=run_id)
        else:
            logging.error('Testplan #%d is is not available', plan_id)
            return False

    else:
        logging.error("You have to indicate a testrun or a testplan ID")
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
        '--config', type=argparse.FileType('r', encoding='UTF-8'), required=True, help='Configuration file')
    parser.add_argument('--dryrun', action='store_true', help='Run script but don\'t publish results')
    parser.add_argument('--password', help='Password of TestRail account')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--run-id', action='store', type=int, default=None, help='Identifier of testrun, that appears in TestRail.')
    group.add_argument(
        '--plan-id', action='store', type=int, default=None, help='Identifier of testplan, that appears in TestRail.')
    return parser.parse_args()


if __name__ == '__main__':
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
    if ARGUMENTS.password:
        PASSWORD = ARGUMENTS.password
    else:
        PASSWORD = CONFIG.get('API', 'password')

    logging.debug('Connection info: URL=%s, EMAIL=%s, PASSWORD=%s', URL, EMAIL, len(PASSWORD) * '*')

    # Init API
    api = TestRailApiUtils(URL)
    api.user = EMAIL
    api.password = PASSWORD

    # Main
    if publish_results(api, TESTCASES, run_id=ARGUMENTS.run_id, plan_id=ARGUMENTS.plan_id):
        print(Fore.GREEN + 'OK')
        sys.exit()
    else:
        print(Fore.LIGHTRED_EX + 'ERROR')
        sys.exit(1)
