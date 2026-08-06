"""``mailtea.__version__`` must not lie.

The version is written twice — ``__version__`` in ``mailtea/__init__.py`` and
``version`` in ``pyproject.toml`` — and only the second is what PyPI publishes.
Nothing tied them together, so a release that bumped the manifest and forgot the
constant would ship 0.7.0 and introduce itself as 0.6.0 forever. Nobody notices,
because the client keeps working perfectly while reporting the wrong number in
every bug report filed against it.

This is the third package in the repo to carry that trap: ``mailtea-cli`` had a
test and it caught a stale ``VERSION`` during the 0.7.0 bump; ``mailtea-mcp`` had
no test and had been introducing itself as "0.2.0" for five releases. So Python
gets one too.
"""

import pathlib
import re
import unittest

import mailtea


class VersionTest(unittest.TestCase):
    def test_version_matches_pyproject(self):
        pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        self.assertIsNotNone(match, "pyproject.toml has no version")
        manifest = match.group(1)
        self.assertEqual(
            mailtea.__version__,
            manifest,
            f"__init__.py says {mailtea.__version__} but pyproject.toml says {manifest}. "
            "PyPI publishes the manifest, so the manifest is right and the constant is stale.",
        )


if __name__ == "__main__":
    unittest.main()
