# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.9-buster

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Chrome
RUN mkdir /usr/bin/chrome \
    && wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \ 
    && dpkg -x ./google-chrome-stable_current_amd64.deb /usr/bin/chrome \
    && rm ./google-chrome-stable_current_amd64.deb

# SET GOOGLE CHROME PATH
ENV PATH="${PATH}:/usr/bin/chrome/opt/google/chrome"


# Set display port as an environment variable
ENV DISPLAY=:99

# Run the application
CMD ["python", "./server.py"]