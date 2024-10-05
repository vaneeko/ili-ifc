# Using Python 3.9-Image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose port and set startup command
EXPOSE 5000
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0"]
