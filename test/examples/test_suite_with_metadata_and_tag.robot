*** Settings ***
Metadata          TEST_CASE_ID    C345

*** Test Cases ***
Test With Id 345 From Metadata
    [Tags]    NONE
    Log    With Metadata

Test With Id 366 From Tag
    [Tags]    TAG1    TAG2    test_case_id=C366
    Log    With Metadata And Tag
