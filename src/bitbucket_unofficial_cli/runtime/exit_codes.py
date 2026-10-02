from enum import IntEnum


# 1 and 2 are reserved by Click for generic failures and usage errors.
class ExitCode(IntEnum):
    OK = 0
    FAILURE = 1
    USAGE = 2
    CONFIGURATION = 3
    AUTHENTICATION = 4
    FORBIDDEN = 5
    NOT_FOUND = 6
    VALIDATION = 7
    RATE_LIMITED = 8
    UNAVAILABLE = 9
