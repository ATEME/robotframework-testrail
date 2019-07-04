*** Test Cases ***
Test With Id 347 From Tag
    [Tags]    TAG1    test_case_id=C347    TAG2
    Fail    Only With Tag

Test With Id 348 From Tag
    [Tags]    TAG1    TAG2    test_case_id=348
    Log    Only With Tag

Test Without Id
    [Tags]    TAG1    TAG2
    Fail    With No Tag
