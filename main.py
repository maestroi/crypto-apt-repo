import os
import requests
import tarfile
import subprocess
import stat
import logging
import json
import time
import shutil
import gzip

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s — %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', handlers=[logging.StreamHandler()])

# Constants
GITHUB_API = "https://api.github.com"
REPO_OWNER = "solana-labs"
REPO_NAME = "solana"
LATEST_RELEASE_ENDPOINT = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
FILE_NAME_PATTERN = "solana-release-x86_64-unknown-linux-gnu.tar.bz2"
BINARIES = ['solana-gossip', 'solana-keygen', 'solana-ledger-tool', 'solana-validator', 'solana']
CRYPTO_BINARY_APT_PATH = 'cryptobinaryapt'

def get_latest_release():
    response = requests.get(LATEST_RELEASE_ENDPOINT)
    if response.status_code != 200:
        raise Exception(f"GitHub API response: {response.status_code}")
    return response.json()

def download_tarball(tarball_url, version):
    version_dir = os.path.join(os.getcwd(), version)
    if not os.path.exists(version_dir):
        os.makedirs(version_dir)

    tarball_path = os.path.join(version_dir, FILE_NAME_PATTERN)
    response = requests.get(tarball_url, stream=True)
    if response.status_code == 200:
        with open(tarball_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        return tarball_path
    else:
        raise Exception(f"Failed to download tarball: {response.status_code}")

def extract_tarball(tarball_path, target_dir):
    with tarfile.open(tarball_path, 'r:bz2') as tar:
        tar.extractall(path=target_dir)
        top_level_dir_name = tar.getnames()[0].split('/')[0]
    return {binary: os.path.join(target_dir, top_level_dir_name, 'bin', binary) for binary in BINARIES}


def build_package(version, binaries):
    try:
        # Load control information
        with open('control.json') as json_file:
            control_info = json.load(json_file)

        # Update version in control info
        control_info['Version'] = version

        package_structure_dir = "solana-rpc"
        temp_package_dir = f"temp_package_{version}"

        # Copy package structure to temp directory
        shutil.copytree(package_structure_dir, temp_package_dir)

        # Create control file in DEBIAN directory
        control_file_path = os.path.join(temp_package_dir, "DEBIAN", "control")
        with open(control_file_path, 'w') as control_file:
            for key, value in control_info.items():
                control_file.write(f"{key}: {value}\n")

        # Copy binaries to the right directory in the temp package
        bin_dir = os.path.join(temp_package_dir, "DEBIAN", "usr", "bin")  # Adjusted to correct path
        for binary, path in binaries.items():
            shutil.copy(path, os.path.join(bin_dir, binary))

        # Build the Debian package
        package_name = f"solana-rpc_{version}_amd64.deb"
        subprocess.run(['dpkg-deb', '--build', temp_package_dir, package_name])

        logging.info(f"Package {package_name} created successfully.")

        # Define the target directory for the .deb file
        target_dir = os.path.join(CRYPTO_BINARY_APT_PATH, "pool", "main", "s", "solana-rpc")
        os.makedirs(target_dir, exist_ok=True)

        # Move the .deb file to the target directory
        shutil.move(package_name, os.path.join(target_dir, package_name))

        # Update the package file
        update_packages_file(target_dir)

        # Clean up
        shutil.rmtree(temp_package_dir)

    except Exception as e:
        logging.error(f"An error occurred: {e}")

def clean_version(version):
    version_dir = os.path.join(os.getcwd(), version)
    shutil.rmtree(version_dir)
    logging.info(f"Removed version directory {version_dir}")


def update_packages_file(pool_dir):
    # Define the directory where the Packages file will be stored
    dists_dir = os.path.join(CRYPTO_BINARY_APT_PATH, "dists", "stable", "main", "binary-amd64")
    os.makedirs(dists_dir, exist_ok=True)
    
    pool_dir = os.path.join(CRYPTO_BINARY_APT_PATH, "pool", "main", "s")

    # Path for the Packages file
    packages_file_path = os.path.join(dists_dir, 'Packages')

    # Generate the Packages file
    with open(packages_file_path, 'w') as packages_file:
        subprocess.run(['dpkg-scanpackages', '.', '/dev/null'], cwd=pool_dir, stdout=packages_file)

    # Compress the Packages file
    with open(packages_file_path, 'rb') as f_in:
        with gzip.open(f'{packages_file_path}.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    logging.info(f"Updated Packages file in {dists_dir}")

def main():
    logging.info("Starting Solana Debian package creation...")

    release = get_latest_release()
    version = release['tag_name'].lstrip('v')
    package_name = f"solana-rpc_{version}_amd64.deb"
    target_dir = os.path.join(CRYPTO_BINARY_APT_PATH, "pool", "main", "s", "solana-rpc")
    package_path = os.path.join(target_dir, package_name)

    # Check if the package already exists
    if os.path.exists(package_path):
        logging.info(f"Package {package_name} already exists. Skipping...")
        return

    tarball_url = next((asset['browser_download_url'] for asset in release['assets'] if asset['name'] == FILE_NAME_PATTERN), None)
    
    if not tarball_url:
        logging.error(f"Asset {FILE_NAME_PATTERN} not found in the latest release.")
        return

    logging.info(f"Downloading tarball for version {version}")
    tarball_path = download_tarball(tarball_url, version)

    logging.info("Extracting binaries")
    binaries = extract_tarball(tarball_path, version)

    logging.info("Building package")
    build_package(version, binaries)
    
    logging.info("Updating Packages file")
    update_packages_file(target_dir)
    
    logging.info("Cleaning up")
    clean_version(version)
    
    logging.info("Done")
    
if __name__ == "__main__":
    logging.info('Service started')
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        logging.info('Sleeping for 1 hour...')
        time.sleep(3600)  # Sleep for 1 hour
