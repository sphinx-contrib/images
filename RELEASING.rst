Releasing sphinxcontrib-images
==============================

1. Test releasing to TestPyPI

   - Bump the package version by editing ``sphinxcontrib/images.py``
     (i.e. from 0.9.2 to 0.9.3rc1 -- use rcN for subsequent releases),
     create a release branch with this change in the
     https://github.com/sphinx-contrib/images repository, and finally create a
     pull request.

   - Trigger `publishing to TestPyPI via the GitHub UI`_ and select the release
     branch as where to run the workflow.

2. Test the TestPyPI release

   - Make a new virtual environment::

        read -p 'Version: ' VERSION \
           && python3 -m venv venv-$VERSION \
           && . venv-$VERSION/bin/activate

   - Install the release (candidate) (see [1]_) and verify that the correct
     version is installed::

        pip install -U \
              --index-url https://test.pypi.org/simple/ \
              --extra-index-url https://pypi.org/simple \
              "sphinxcontrib-images >= $VERSION.dev0" \
           && pip freeze | grep sphinxcontrib-images

   - Verify the release candidate can build the package docs in docs/::

        cd docs/ && make html

3. Finally test releasing the actual release to TestPyPI:

   Repeat the previous steps but without rcN in the version number, e.g.
   change 0.9.3rc1 to 0.9.3

4. Merge the release PR with GitHub's "squash merge", tag the release commit,
   and push the tag to GitHub to trigger a release to PyPI

.. [1] `Alternate "rc" spellings`_ ("c", "pre", "preview") are normalized to
   "rc", so version ``0.9.3pre1`` is converted to ``0.9.3rc1``. To reduce
   confusion when installing the RC package use "rcN" for the version number
   suffix. This allows using the same version when installing with ``pip``
   (i.e.  ``pip install sphinxcontrib-images==0.9.3rc1``).

   If you release to TestPyPI in this order: 0.9.3rc1 - 0.9.3rc2 - 0.9.3
   then you should be able to test all three versions by upgrading over the
   previous versions with the provided command.

.. _Alternate "rc" spellings: https://peps.python.org/pep-0440/#pre-release-spelling
.. _publishing to TestPyPI via the GitHub UI: https://github.com/sphinx-contrib/images/actions/workflows/test-publish.yml
