# crypto-apt-repo

This project is created to play around with debian packages and apt repositories.
Just wanted to learn how this works and how to create a repository for my own packages.

## Features

- Creates a debian package
- Creates a apt repository
- Hosts the apt repository
- Installs the package from the repository

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have a `Linux` machine with Docker and Docker-Compose installed.
- You have basic knowledge of Docker and containerization.

## Getting Started

These instructions will get your copy of the project up and running on your local machine for development and testing purposes.

### Installation

To install crypto-apt-repo, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/maestroi/crypto-apt-repo.git
```

2. Navigate to the project directory:
```bash
cd crypto-apt-repo
```

3. Start service
```bash	
docker-compose up -d
```	

## Configuration
Describe any configuration files and how to modify them, for instance:

`control.json`: Modify this file to set up the Debian package metadata.
`docker-compose.yml`: Contains the configuration for Docker services.

## Usage
Provide instructions on how to use your project, for example:

To build and host your Debian packages using the package-builder service:
```bash
# This will start the build process and host your packages
docker-compose up -d package-builder
```

## Setup a repository
```bash
echo "deb [trusted=yes] http://apt.beardsoft.io/ stable main" | sudo tee /etc/apt/sources.list.d/beardsoft.list
sudo apt update
```

## Contributing to crypto-apt-repo
To contribute to crypto-apt-repo, follow these steps:

1. Fork this repository.
2. Create a branch: git checkout -b <branch_name>.
3. Make your changes and commit them: git commit -m '<commit_message>'
4. Push to the original branch: git push origin <project_name>/<location>
5. Create the pull request.


## Maintainers
This project is currently maintained by:

@maestroi
