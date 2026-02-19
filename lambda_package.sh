#!/bin/bash
# Lambda package script for creating deployment packages

set -e

# Check if function name provided
if [ -z "$1" ]; then
    echo "Usage: ./lambda_package.sh <handler_name>"
    echo "Example: ./lambda_package.sh analytics_handler"
    exit 1
fi

HANDLER_NAME=$1
PACKAGE_NAME="lambda-${HANDLER_NAME}.zip"

echo "Creating Lambda deployment package for ${HANDLER_NAME}..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: ${TEMP_DIR}"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t "${TEMP_DIR}" --quiet

# Copy source code
echo "Copying source code..."
cp -r src/ "${TEMP_DIR}/"

# Create zip file
echo "Creating zip file..."
cd "${TEMP_DIR}"
zip -r "${PACKAGE_NAME}" . -q
cd -

# Move zip to project root
mv "${TEMP_DIR}/${PACKAGE_NAME}" .

# Cleanup
rm -rf "${TEMP_DIR}"

echo "Package created: ${PACKAGE_NAME}"
echo "Size: $(du -h ${PACKAGE_NAME} | cut -f1)"
