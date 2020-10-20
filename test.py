import os
import unittest
import coverage


if __name__ == '__main__':
    cov = coverage.coverage(
        omit=[
            'venv/*', '/usr/*', '*/tests/*',
            'test.py', '*/__init__.py'
        ]
    )
    cov.start()

    tests = unittest.TestLoader().discover('vote/tests')
    result = unittest.TextTestRunner(verbosity=2).run(tests)

    if result.wasSuccessful():
        cov.stop()
        cov.save()

        print('Coverage Summary:')
        cov.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        cov.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        cov.erase()
    else:
        print('Error in running tests.')
