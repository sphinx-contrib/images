#!/bin/sh

V1=$(sed -nE "s/^.*version.*=.*([0-9]+\.[0-9]+\.[0-9]+(\.[a-z0-9]+)?).*$/\1/p" pyproject.toml)
V2=$(sed -nE "s/^.*version.*=.*([0-9]+\.[0-9]+\.[0-9]+(\.[a-z0-9]+)?).*$/\1/p" sphinxcontrib/images.py)
SUB=$(git submodule status sphinxcontrib_images_lightbox2/lightbox2 | cut -c1)

printf "\n## RELEASE SPHINXCONTRIB-IMAGES TO PYPI ##\n\n"

printf "# VERSION CHECK #\n"
printf "pyproject.toml: %s\n" "$V1"
printf "sphinxcontrib/images.py: %s\n" "$V2"

if [ "$V1" != "$V2" ]; then
    printf "ERROR: versions do _not_ match\n\n"
else
    printf "SUCCESS: Versions match\n\n"
fi

printf "# SUBMODULE STATUS #\n"
if [ "$SUB" = "-" ]; then
    echo "ERROR: lightbox2 submodule _not_ initialized"
else
    echo "SUCCESS: lightbox2 submodule initialized"
fi

printf "Press [Enter] for instructions ..." 
read ANSWER

cat <<STEPS


# 1. Clone lightbox2 submodule:
git submodule update --init --recursive


# 2. Create a virtual environment and install build & twine
python -m venv venv-twine 
source venv-twine/bin/activate
pip install build twine

# 3. Test release to TestPyPI
 - Requires registration at https://test.pypi.org/account/register/ 

 - Bump version by editing setup.py and sphinxcontrib/images.py 
   e.g. from 0.9.2 to 0.9.3.pre1 (use .pre2 second test release etc.) 

 - Remove old distributions/builds
rm -r dist/ build/

 - Build the distribution (this can also be done by \`tox -e wheel\`)
python -m build --wheel

 - Upload to TestPyPI
twine upload -r testpypi dist/*


# 4. Test the TestPyPI-release
 - Make a new virtual environment
python -m venv venv-0.9.3.pre1

 - Install the prerelease (see note [1])
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple sphinxcontrib-images

 - Verify the version installed:
pip freeze | grep sphinxcontrib-images

 - Verify the prereleased package can build the package docs in docs/
cd docs/
make html 

 - If anything fails repeat step 3. and 4.


# 5. Final test release to TestPyPI
 - Repeat step 3. and 4. but without .preN in the version number,
   e.g. change 0.9.3.pre1 to 0.9.3


# 6. Release to PyPI
 - Requires user with maintainer status on the package
   https://pypi.org/project/sphinxcontrib-images/

 - Upload to PyPI
twine upload dist/*

# 7. Commit released version, tag and push
git add project.toml sphinxcontrib/images.py
git commit -m "Version bumped to a.b.c"
git tag -a a.b.c -m "Release a.b.c"
git push origin master
git push origin a.b.c


[1] Version 0.9.3.pre1 in setup.py is converted to 0.9.3rc1 in TestPyPI
    so to install a specific version of the prerelese use 
    'sphinxcontrib-images==0.9.3rc1' with pip.

    If you release to TestPyPI in this order: 0.9.3.pre1 - 0.9.3.pre2 - 0.9.3
    then you should be able to test all three versions by simply installing the 
    package without stating the version since 0.9.3.pre2 > 0.9.3.pre1 and 
    0.9.3 > 0.9.3.pre2
    
STEPS