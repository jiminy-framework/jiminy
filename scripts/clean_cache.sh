#!/usr/bin/env bash

echo "----------------------------------"
echo "Cleaning Jiminy repository"
echo "----------------------------------"

echo ""
echo "Removing Python caches..."

find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

echo ""
echo "Removing pytest cache..."

rm -rf .pytest_cache

echo ""
echo "Removing Graphviz outputs..."

find . -type f -name "*.png" -delete
find . -type f -name "*.svg" -delete
find . -type f -name "*.dot" -delete

echo ""
echo "Removing notebook checkpoints..."

find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +

echo ""
echo "Removing build artifacts..."

rm -rf build
rm -rf dist
rm -rf *.egg-info

echo ""
echo "Clean completed."
echo "----------------------------------"