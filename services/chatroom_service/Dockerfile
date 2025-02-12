# Use Python base image
FROM python:3.13.1

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port
EXPOSE 5003

# Run the service
CMD ["python", "chatroom.py"]
