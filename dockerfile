# Use the official Python image from the Docker Hub
FROM python:3.10-slim 

# Set the working directory in the container
WORKDIR /app

# Copy the environment.yml file to the working directory
COPY wastewater_qpcr_app/requirements.txt .

RUN pip install -r requirements.txt

# Copy the application code to the working directory
COPY wastewater_qpcr_app/ .

# Set the entry point to run the application
CMD gunicorn -b 0.0.0.0:8765 app:server
