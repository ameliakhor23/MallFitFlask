# Specify the base image
FROM mcr.microsoft.com/azure-functions/python:4

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port the app will run on
EXPOSE 7071

# Command to run the app
CMD ["python", "app.py"]
