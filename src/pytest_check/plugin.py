import sys
import pytest
from colorama import just_fix_windows_console
from _pytest._code.code import ExceptionInfo
from . import check_functions
from . import context_manager
from . import check_log
from . import pseudo_traceback
from . import check_raises


from _pytest.skipping import xfailed_key


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    failures = check_log.get_failures()
    check_log.clear_failures()

    if failures:
        if item._store[xfailed_key]:
            report.outcome = "skipped"
            report.wasxfail = item._store[xfailed_key].reason
        else:

            summary = "Failed Checks: {}".format(len(failures))
            longrepr = ["\n".join(failures)]
            longrepr.append("-" * 60)
            longrepr.append(summary)

            if report.longrepr:
                longrepr.append("-" * 60)
                longrepr.append(report.longreprtext)
                report.longrepr = "\n".join(longrepr)
            else:
                report.longrepr = "\n".join(longrepr)
            report.outcome = "failed"
            try:
                raise AssertionError(report.longrepr)
            except AssertionError:
                excinfo = ExceptionInfo.from_current()
            call.excinfo = excinfo


def pytest_configure(config):
    # Add some red to the failure output, if stdout can accommodate it.
    isatty = sys.stdout.isatty()
    color = config.option.color
    check_log.should_use_color = (isatty and color == "auto") or (
        color == "yes"
    )
    just_fix_windows_console()

    # If -x or --maxfail=1, then stop on the first failed check
    # Otherwise, let pytest stop on the maxfail-th test function failure
    maxfail = config.getvalue("maxfail")
    stop_on_fail = maxfail == 1
    check_functions.set_stop_on_fail(stop_on_fail)
    context_manager._stop_on_fail = stop_on_fail
    check_raises._stop_on_fail = stop_on_fail

    # Allow for --tb=no to turn off check's pseudo tbs
    traceback_style = config.getvalue("tbstyle")
    pseudo_traceback._traceback_style = traceback_style


# Allow for tests to grab "check" via fixture:
# def test_a(check):
#    check.equal(a, b)
@pytest.fixture(name="check")
def check_fixture():
    # return check_functions
    return context_manager.check
