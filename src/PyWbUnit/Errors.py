# -*- coding: utf-8 -*-
import re
import sys


class UnboundNameException(NameError):

    def __init__(self, msg):
        NameError.__init__(self, msg)


class CommandArgumentException(ValueError):

    def __init__(self, msg):
        ValueError.__init__(self, msg)


class MissingMemberException(AttributeError):

    def __init__(self, msg):
        AttributeError.__init__(self, msg)


class CoWbUnitRuntimeError(RuntimeError):

    def __init__(self, msg):
        RuntimeError.__init__(self, msg)


class CommandFailedException(RuntimeError):

    def __init__(self, msg):
        RuntimeError.__init__(self, msg)


class TooManyArgumentsException(ValueError):

    def __init__(self, msg):
        ValueError.__init__(self, msg)


def handleException(msg):
    try:
        errorType, message = re.search(r'(\w*Exception):\s*(\w+.*)', msg).groups()
        errorModule = sys.modules[__name__]
        return getattr(errorModule, errorType, Exception)(message.strip())
    except AttributeError:
        return Exception(msg)
