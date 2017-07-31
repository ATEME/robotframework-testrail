robotframework-testrail
=======================

Current status: beta

This script publishes results of Robot Framework in TestRail.

The standard process is:
Robot Framework execution => `output.xml` => This script => TestRail API


Installation
------------

Best use with `virtualenv` with Python>=3:
    
    > virtualenv .
    > Scripts\activate  # Windows case
    > pip install -r requirements.txt


Configuration
-------------

### Robot Framework

Create a metadata `TEST_CASE_ID` in your test suite containing TestRail ID.

Format of `TEST_CASE_ID` is :
* Descriptor + an integer: `C1234`, `TestRail5678`
* An integer: 1234, 5678

**Example**:
```robotframework
*** Settings ***
Metadata          TEST_CASE_ID    C345

*** Test Cases ***

Test Example
    Log    ${SUITE METADATA['TEST_CASE_ID']}
```

In this case, the result of Test Case C345 will be 'passed' in TestRail.

### TestRail configuration

Create a configuration file (`testrail.cfg` for instance) containing following parameters:

```ini
[API]
url = https://yoururl.testrail.net/
email = user@email.com
api_key = <api_key> # May be set in command line
```

Usage
-----

```
usage: robotframework2testrail.py [-h] --config CONFIG [--dryrun]
                                  [--api-key API_KEY]
                                  (--run-id RUN_ID | --plan-id PLAN_ID)
                                  xml_robotfwk_output

Tool to publish Robot Framework results in TestRail

positional arguments:
  xml_robotfwk_output  XML output results of Robot Framework

optional arguments:
  -h, --help           show this help message and exit
  --config CONFIG      Configuration file
  --dryrun             Run script but don't publish results
  --api-key API_KEY    API key of TestRail account with write access
  --run-id RUN_ID      Identifier of Test Run, that appears in TestRail.
  --plan-id PLAN_ID    Identifier of Test Plan, that appears in TestRail.
```

### Example

```bash
# Dry run
python robotframework2testrail.py --config=testrail.cfg --dryrun --run-id=196 output.xml

# Publish in Test Run #196
python robotframework2testrail.py --config=testrail.cfg --run-id=196 output.xml

# Publish in Test Plan #200
python robotframework2testrail.py --config=testrail.cfg --plan-id=200 output.xml

# Publish with api key in command line
python robotframework2testrail.py --config=testrail.cfg --api-key azertyazertyqsdfqsdf --plan-id=200 output.xml
```
