"""Run the offline suite test by test and name every test after which something under a home directory changed (revision 9,
20 Oct 2026). Run it from the root of a checkout: `python find_home_writers.py`.

HOME is set to a new empty directory before the suite is imported. Watched after every test: that directory and, when the suite's
isolation moves HOME somewhere else (tests/_isolation.py since the fix of 20 Oct), the directory HOME points to at that moment. A
test that writes into either, or a subprocess it starts, is listed with the paths it changed. The suite's own result is printed too.
"""
import os
import sys
import tempfile
import unittest

probe_home = tempfile.mkdtemp(prefix="attest-home-probe-")
os.environ["HOME"] = probe_home
for name in ("XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"):
    os.environ.pop(name, None)
sys.path.insert(0, os.getcwd())


def watched() -> list[str]:
    return sorted({probe_home, os.environ.get("HOME", probe_home)})


def snapshot() -> dict:
    seen = {}
    for top in watched():
        for root, dirs, files in os.walk(top):
            for name in files + dirs:
                path = os.path.join(root, name)
                try:
                    st = os.lstat(path)
                except OSError:
                    continue
                seen[path] = (st.st_mtime_ns, st.st_size)
    return seen


def label(path: str) -> str:
    for top, name in ((probe_home, "<probe HOME>"), (os.environ.get("HOME", ""), "<suite HOME>")):
        if top and path.startswith(top + os.sep):
            return f"{name}/{os.path.relpath(path, top)}"
    return path


class Probe(unittest.TextTestResult):
    def startTest(self, test):
        self._before = snapshot()
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        after = snapshot()
        changed = sorted(p for p in after if self._before.get(p) != after[p])
        if changed:
            WRITERS.append((test.id(), [label(p) for p in changed]))


WRITERS: list = []
suite = unittest.defaultTestLoader.discover("tests", top_level_dir=".")
with open(os.devnull, "w") as sink:
    result = unittest.TextTestRunner(resultclass=Probe, verbosity=0, stream=sink).run(suite)
print(f"ran {result.testsRun}, failures {len(result.failures)}, errors {len(result.errors)}, skipped {len(result.skipped)}")
print(f"HOME during the suite: {'the probe directory' if os.environ.get('HOME') == probe_home else 'moved by the suite to its own new directory'}")
print(f"tests that wrote under a home directory: {len(WRITERS)}")
for test_id, paths in WRITERS:
    print(test_id)
    for p in paths:
        print("    ", p)
for failure in result.failures + result.errors:
    print("FAILED", failure[0].id())
