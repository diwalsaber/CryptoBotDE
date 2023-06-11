FROM python:3.9
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

# Run the command on container startup
CMD [ "python", "binance_to_db.py" ]
