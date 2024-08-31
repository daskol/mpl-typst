#!/usr/bin/env bash
# TODO(@dakol): We should wrap this script into action for convinient use with
# GitHub Actions.

function name-status() {
    git diff --name-only main..$branch -- "$@"
}

branch=$1
if [ -z "$branch" ]; then
    branch=$(git branch --show-current)
    echo "no branch specified: assume current branch is $branch"
fi

# What pure python modules are changed in this PR?
name-status 'mpl_typst/**/*.py' >> changed.txt

# What python modules are changed in this PR?
echo ':: Changed python modules'
cat changed.txt

# What python tests are affected in this PR?
: > affected.txt
pytest-dirty changed.txt affected.txt
echo ':: Affected python tests'
cat affected.txt

# Run tests affected by this PR.
if [ -s affected.txt ]; then
    pytest -vv \
        --cov=mpl_typst \
        --cov-report=html:coverage/html/${PYTHON_TAG} \
        --cov-report=xml:coverage/xml/report.${PYTHON_TAG}.xml \
        --junitxml=pytest/report.${PYTHON_TAG}.xml \
        @affected.txt
else
    echo ':: No tests affected'
fi
