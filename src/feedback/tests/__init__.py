# coding=utf-8

from django.utils.translation import get_language

#TODO: Aufruf einzelner Tests möglich machen

def suite():
    import glob
    from os.path import dirname, basename, splitext, sep
    from django.utils import unittest


    suite = unittest.TestSuite()

    # find all test files in this directory
    for test_file in glob.glob(dirname(__file__) + sep + 'test_*.py'):

        # get filename without '.py' of test file
        test_name = splitext(basename(test_file))[0]

        # calculate module name of test file
        test_module = __name__ + '.' + test_name

        # add all tests from test file to our test suite
        suite.addTest(unittest.TestLoader().loadTestsFromName(test_module))
    return suite

LOGIN_END = f'/{get_language()}/feedback/intern/'
INDEX_END = f'/{get_language()}/feedback/intern/uebersicht/'
AUTH_END = f'/{get_language()}/feedback/intern/auth_user/'
TESTSERVER_BEGIN = ''
LOGIN_URL = TESTSERVER_BEGIN+LOGIN_END
INDEX_URL = TESTSERVER_BEGIN+INDEX_END
AUTH_URL = TESTSERVER_BEGIN+AUTH_END
