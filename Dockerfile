# Use a base image with Python and the necessary tools installed
FROM python:3.9-slim

# Install dpkg-dev for dpkg-scanpackages
RUN apt-get update && apt-get install -y dpkg-dev

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script, JSON control file, and any other necessary files
COPY main.py requirements.txt ./

# Install any necessary Python packages
RUN pip install -r requirements.txt

# Run the script to build the Debian package
CMD ["python", "main.py"]
