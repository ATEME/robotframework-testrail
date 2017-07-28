#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""" Tool to publish Robot Framework results in TestRail """
import argparse
import configparser
import logging
import os
import sys

from colorama import Fore, init
from lxml import etree

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


def update_testcases(run_id, plan_id):
    pass


def pretty_print(testcases):
    """ Pretty print of testcases """
    msg_template = '{id}\t{status}\t{name}'
    for testcase in testcases:
        if testcase['status'] == 'PASS':
            print(Fore.GREEN + msg_template.format(**testcase), end='')
        else:
            print(Fore.RED + msg_template.format(**testcase), end='')
        print(Fore.RESET)


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
    parser.add_argument('--dryrun', action='store_false', help='Run script but don\'t publish results')
    parser.add_argument('--password', help='Password of TestRail account')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run-id', action='store', default=0, help='Identifier of testrun, that appears in TestRail.')
    group.add_argument('--plan-id', action='store', default=0, help='Identifier of testplan, that appears in TestRail.')
    return parser.parse_args()


if __name__ == '__main__':
    # Manage options
    ARGUMENTS = options()

    logging.debug('Command line arguments: %s', ARGUMENTS)

    if ARGUMENTS.dryrun:
        testcases = get_testcases(ARGUMENTS.xml_robotfwk_output[0].name)
        pretty_print(testcases)

    # Init global variables
    config = configparser.ConfigParser()
    config.read_file(ARGUMENTS.config)
    URL = config.get('API', 'url')
    EMAIL = config.get('API', 'email')
    if ARGUMENTS.password:
        PASSWORD = ARGUMENTS.password
    else:
        PASSWORD = config.get('API', 'password')

    logging.debug('Connection info: URL={}, EMAIL={}, PASSWORD={}'.format(URL, EMAIL, len(PASSWORD) * '*'))
