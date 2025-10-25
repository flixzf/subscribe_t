# Use a base Python image
FROM python:3.10-slim

# Install system dependencies, including those for GPG key management
RUN apt-get update && apt-get install -y wget gnupg

# Add the Google Chrome GPG key
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg

# Add the Google Chrome repository
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list

# Update apt and install Google Chrome
RUN apt-get update \
    && apt-get install -y google-chrome-stable

# Set up a working directory
WORKDIR /app

# Copy the requirements file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the script
CMD ["python", "tistory_automation.py"]