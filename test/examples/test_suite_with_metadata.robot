*** Settings ***
Metadata          TEST_CASE_ID    C344

*** Test Cases ***
Test With Id_344 From Metadata
    [Tags]    NONE
    Log    Only With Metadata

Test2 With Id_344 From Metadata
    [Tags]    NONE
    Fail   Only With Metadata
