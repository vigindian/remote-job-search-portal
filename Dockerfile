# python:3.9-slim as the base image
FROM python:3.9-slim

# working directory where the Docker container will run
WORKDIR /app

# Copying all the application files to the working directory, excluding files in .dockerignore
COPY . .

# Install all the dependencies
RUN pip install -r requirements.txt

# First-run of jobs_scraper to scrape job details as per your JOB_SITES config in localenv.py
RUN python /app/jobs_scraper.py

# Expose application port
EXPOSE 4015

# The command required to run the Dockerized application
CMD ["python", "/app/app.py"]
