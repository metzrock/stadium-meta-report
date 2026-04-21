#!/bin/bash
set -e

# Generate new issue
DATE=$(date +%Y-%m-%d)
ISSUE_FILE="issues/issue_${DATE}.md"

echo "Generating issue for ${DATE}..."
python3 generate_issue.py -o "${ISSUE_FILE}"

if [ ! -s "${ISSUE_FILE}" ]; then
    echo "ERROR: Issue file is empty or missing"
    exit 1
fi

echo "Issue generated: ${ISSUE_FILE} ($(wc -l < ${ISSUE_FILE}) lines)"

# Build static site
echo "Building static site..."
python3 build_site.py

# Deploy to gh-pages
echo "Deploying to GitHub Pages..."
DEPLOY_DIR=$(mktemp -d)
cp -r site/* "${DEPLOY_DIR}/"
# Also copy markdown source for archives
cp "${ISSUE_FILE}" "${DEPLOY_DIR}/"

cd "${DEPLOY_DIR}"
git init
git config user.email "hermes@local"
git config user.name "Hermes"
git remote add origin https://github.com/metzrock/stadium-meta-report.git
git checkout -b gh-pages
git add .
git commit -m "Issue #$(date +%U) — ${DATE}"
git push origin gh-pages --force

cd -
rm -rf "${DEPLOY_DIR}"

# Commit source to main
git add issues/ "${ISSUE_FILE}" 2>/dev/null || true
git add .
git commit -m "Issue for ${DATE}" --allow-empty
git push origin main

echo "Done. Live at: https://metzrock.github.io/stadium-meta-report/"
