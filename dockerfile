# Use the official Python image from the Docker Hub
FROM condaforge/miniforge3

# Set the working directory in the container
WORKDIR /app

# Copy the environment.yml file to the working directory
COPY wastewater_qpcr_app/environment.yml .

RUN conda init && \
    mamba env create -f environment.yml && \
    mamba clean -afy

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "rapter-env", "/bin/bash", "-c"]

# Copy the application code to the working directory
COPY wastewater_qpcr_app/ .

# Set the entry point to run the application
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "rapter-env", "python", "app.py"]

# docker run \
#             --rm \
#             -p 8765:8765 \
#             -v "/{PATH}/wastewater_qpcr.github/data:/app/assets/data" \
#             -e "MAXMEM=8000" \
#             poeli/wastewater_qpcr_app:latest