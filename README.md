robotframework-testrail
=======================

This script publishes results of Robot Framework in TestRail.

The standard process is:
Robot Framework execution => `output.xml` => This script => TestRail API


Installation
------------

Tested with Python>=3.

Best use with `virtualenv` (to adapt according your Python/OS version):
    
```cmd
> virtualenv .
> Scripts\activate  # Windows case
> pip install -r requirements.txt
```


Configuration
-------------

### Robot Framework

To create the `TEST_CASE_ID`  you have the possibility to use the metadata or the test's tag, `the priority is done to the tag and not the metadata`.


**With Metadata:**

If you want to create only one `TEST_CASE_ID` for you test, use the following method:

Create a metadata `TEST_CASE_ID` in your test containing TestRail ID.

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


**With Tags:**

If you want to create one or more than `TEST_CASE_ID` for your test or tests use the following method:

Create a tag `test_case_id=ID` in your test containing TestRail ID without a metadata `TEST_CASE_ID`.

Format of ID is:
* `C` + an integer: `C1234`
* An integer: 1234, 5678

**Example one test**:
```robotframework
*** Test Cases ***
Test 1
    [Tags]  test_case_id=1234   critical standard
```

**Example more than one test**:
```robotframework
*** Test Cases ***
Test 1
    [Tags]  test_case_id=C1234   critical standard
    
Test 2
    [Tags]  test_case_id=C5678   critical standard
    
Test 3
    [Tags]  test_case_id=C91011   critical standard
```
In this case, the results of Test 1 C1234 and Test 2 C5678 and Test 3 C91011 will be 'passed' in TestRail.

**Example priority management**:
```robotframework
*** Settings ***
Metadata          TEST_CASE_ID    C345

*** Test Cases ***

Test Example
Test 1
    [Tags]  test_case_id=C1234   critical standard
```
In this case, the result of Test Case C1234 will be 'passed' in TestRail and not C345, priority to tag and not metatdata.

**Other examples**
You can find more examples in `test/examples` folder.

### TestRail configuration

Create a configuration file (`testrail.cfg` for instance) containing following parameters:

```ini
[API]
url = https://yoururl.testrail.net/
email = user@email.com
password = <api_key> # May be set in command line
```

**Note** : `password` is an API key that should be generated with your TestRail account in "My Settings" section.

Usage
-----

```
usage: robotframework2testrail.py [-h] --tr-config CONFIG
                                  [--tr-password API_KEY]
                                  [--tr-version VERSION] [--dryrun]
                                  [--tr-dont-publish-blocked]
                                  (--tr-run-id RUN_ID | --tr-plan-id PLAN_ID)
                                  xml_robotfwk_output

Tool to publish Robot Framework results in TestRail

positional arguments:
  xml_robotfwk_output   XML output results of Robot Framework

optional arguments:
  -h, --help            show this help message and exit
  --tr-config CONFIG    TestRail configuration file.
  --tr-password API_KEY
                        API key of TestRail account with write access.
  --tr-version VERSION  Indicate a version in Test Case result.
  --dryrun              Run script but don't publish results.
  --tr-dont-publish-blocked
                        Do not publish results of "blocked" testcases in
                        TestRail.
  --tr-run-id RUN_ID    Identifier of Test Run, that appears in TestRail.
  --tr-plan-id PLAN_ID  Identifier of Test Plan, that appears in TestRail.
```

### Example

```bash
# Dry run
python robotframework2testrail.py --tr-config=testrail.cfg --dryrun --tr-run-id=196 output.xml

# Publish in Test Run #196
python robotframework2testrail.py --tr-config=testrail.cfg --tr-run-id=196 output.xml

# Publish in Test Plan #200 and dont publish "blocked" Test Cases in TestRail
python robotframework2testrail.py --tr-config=testrail.cfg --tr-plan-id=200 --tr-dont-publish-blocked output.xml

# Publish in Test Plan #200 with version '1.0.2'
python robotframework2testrail.py --tr-config=testrail.cfg --tr-plan-id=200 --tr-version=1.0.2 output.xml

# Publish with api key in command line
python robotframework2testrail.py --tr-config=testrail.cfg --tr-password azertyazertyqsdfqsdf --tr-plan-id=200 output.xml

```
