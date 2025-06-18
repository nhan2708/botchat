# Base image
FROM python:3.11-slim

# Cài g++ để build psycopg2 nếu cần
RUN apt-get update && apt-get install -y gcc

# Tạo thư mục app
WORKDIR /app

# Copy code và cài thư viện
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Mở cổng
EXPOSE 5000

# Chạy app bằng gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
