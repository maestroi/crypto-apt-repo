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
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s — %(message)s',
                    datefmt='%Y-%m-%d_%H:%M:%S',
                    handlers=[logging.StreamHandler()])

# Constants
GITHUB_API = "https://api.github.com"
REPO_OWNER = "solana-labs"
REPO_NAME = "solana"
LATEST_RELEASE_ENDPOINT = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
FILE_NAME_PATTERN = "solana-release-x86_64-unknown-linux-gnu.tar.bz2"

def get_latest_release():
    response = requests.get(LATEST_RELEASE_ENDPOINT)
    if response.status_code != 200:
        raise Exception(f"GitHub API response: {response.status_code}")
    return response.json()

def download_tarball(tarball_url, version):
    tarball_path = os.path.join(version, FILE_NAME_PATTERN)
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
        # Store the directory name before the TarFile object is closed
        top_level_dir_name = tar.getnames()[0]
    # Return the path to the solana-validator executable
    return os.path.join(target_dir, top_level_dir_name, 'bin', 'solana-validator')

def create_debian_package(version, validator_path, control_info):
    try:
        # Ensure version does not have 'v' prefix
        debian_version = version.lstrip('v')
        control_info['Version'] = debian_version

        # Construct the package file name
        package_name = f"{control_info['Package']}_{debian_version}_{control_info['Architecture']}"

        # Define directories and file paths
        base_dir = "/cryptobinaryapt"
        pool_dir = os.path.join(base_dir, "pool", "main", "s", "solana-validator")
        package_dir = os.path.join(base_dir,package_name)
        debian_dir = os.path.join(package_dir, "DEBIAN")
        bin_dir = os.path.join(package_dir, "usr", "local", "bin")

        # Create necessary directories
        os.makedirs(debian_dir, exist_ok=True)
        os.makedirs(bin_dir, exist_ok=True)
        os.makedirs(pool_dir, exist_ok=True)  # Make sure the pool directory exists

        # Create control file
        control_content = "\n".join(f"{key}: {value}" for key, value in control_info.items()) + "\n"
        with open(os.path.join(debian_dir, "control"), 'w') as control_file:
            control_file.write(control_content)

        # Move the validator binary to the package directory
        shutil.move(validator_path, os.path.join(bin_dir, 'solana-validator'))

        # Set the permissions for the package directory
        set_permissions(package_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH,
                        stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

        # Build the Debian package
        subprocess.run(['dpkg-deb', '--build', package_dir])

        # Locate the .deb file and move it to the pool directory
        deb_file_name = f"{package_name}.deb"
        deb_file_path = os.path.join(base_dir, deb_file_name)
        shutil.move(deb_file_path, pool_dir)
        logging.info(f"Debian package for version {debian_version} created at {pool_dir}/{deb_file_name}")

        # Run dpkg-scanpackages to generate the Packages file
        dists_dir = os.path.join(base_dir, "dists")
        os.makedirs(dists_dir, exist_ok=True)
        
        # Update package file
        update_packages_file(pool_dir, dists_dir)
        shutil.rmtree(package_dir)  # Remove the package directory

        logging.info(f"Updated Packages file in {dists_dir}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def set_permissions(path, dir_perms, file_perms):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), dir_perms)
        for f in files:
            os.chmod(os.path.join(root, f), file_perms)


def package_exists(version, pool_dir):
    # Define the expected .deb file name based on the version
    deb_file_name = f"solana-validator_{version}_amd64.deb"

    # Check if the .deb package already exists
    deb_file_path = os.path.join(pool_dir, deb_file_name)
    return os.path.isfile(deb_file_path)

def update_packages_file(pool_dir, dists_dir):
    # Ensure the directory structure exists
    arch_dir = os.path.join(dists_dir, 'stable', 'main', 'binary-amd64')
    os.makedirs(arch_dir, exist_ok=True)
    
    # Path for the Packages file
    packages_file_path = os.path.join(arch_dir, 'Packages')

    # Generate the Packages file
    with open(packages_file_path, 'w') as packages_file:
        subprocess.run(['dpkg-scanpackages', '.', '/dev/null'], cwd=pool_dir, stdout=packages_file)

    # Compress the Packages file
    with open(packages_file_path, 'rb') as f_in:
        with gzip.open(f'{packages_file_path}.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    logging.info(f"Updated Packages file in {arch_dir}")

def main():
    logging.info('Starting Solana Debian package creation...')
    with open('control.json') as json_file:
        control_info = json.load(json_file)

    release = get_latest_release()
    logging.info(f"Latest release found: {release['tag_name']}")
    tarball_url = next((asset['browser_download_url'] for asset in release['assets'] if asset['name'] == FILE_NAME_PATTERN), None)
    if not tarball_url:
        logging.error(f"Asset {FILE_NAME_PATTERN} not found in the latest release.")
        raise Exception(f"Asset {FILE_NAME_PATTERN} not found in the latest release.")

    latest_version = release['tag_name']
    debian_version = latest_version.lstrip('v')
    
    # Define the output package directory based on the version
    package_dir = f"solana-validator_{debian_version}_amd64"    
    deb_file_name = f"{package_dir}.deb"

    # Define the pool directory where .deb packages are stored
    base_dir = "/cryptobinaryapt"
    pool_dir = os.path.join(base_dir, "pool", "main", "s", "solana-validator")

    # Check if the .deb package already exists
    if package_exists(debian_version, pool_dir):
        logging.info(f"Package for version {debian_version} already exists. Skipping package creation.")
        return  # Skip the rest of the function
    
    logging.info(f"Creating directory for version: {latest_version}")
    os.makedirs(latest_version, exist_ok=True)

    logging.info(f"Downloading tarball from: {tarball_url}")
    tarball_path = download_tarball(tarball_url, latest_version)

    logging.info(f"Extracting tarball to directory: {latest_version}")
    validator_path = extract_tarball(tarball_path, latest_version)

    logging.info(f"Creating Debian package for version: {latest_version}")
    create_debian_package(latest_version, validator_path, control_info)

    logging.info(f"Debian package for version {latest_version} created successfully")


if __name__ == "__main__":
    logging.info('Service started')
    while True:
        try:
            main()
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        logging.info('Sleeping for 1 hour...')
        time.sleep(3600)  # Sleep for 1 hour
