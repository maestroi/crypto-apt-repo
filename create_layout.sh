#!/bin/bash

# Set the name of your distribution
distribution="stable" # Change this to your preferred distribution name

# Create the main directory for the repository
repo_dir="cryptobinaryapt"
mkdir -p "${repo_dir}"

# Create the 'dists' directory structure
dists_dir="${repo_dir}/dists/${distribution}"
mkdir -p "${dists_dir}/main/binary-amd64"

# Create the 'pool' directory structure
pool_dir="${repo_dir}/pool/main"
mkdir -p "${pool_dir}"

# Output the directory structure (optional)
echo "APT repository directory structure:"
tree "${repo_dir}"
