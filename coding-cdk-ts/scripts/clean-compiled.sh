#!/bin/bash
# Clean compiled .js and .d.ts files from CDK source directories
# Run from the CDK project root (e.g., aws-cdk/)
#
# Usage: bash .kiro/skills/coding-cdk-ts/scripts/clean-compiled.sh

set -e

echo "=== Cleaning compiled files ==="
find lib bin config -name "*.js" -o -name "*.d.ts" | xargs rm -f 2>/dev/null || true
echo "=== Done ==="
