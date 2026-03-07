FROM clockworksoul/zork1 AS game

FROM python:3.12-slim

# Copy frotz and game data from the zork1 image
COPY --from=game /usr/bin/frotz /usr/bin/frotz
COPY --from=game /home/frotz/DATA/ZORK1.DAT /home/frotz/DATA/ZORK1.DAT

# Set up save directory
RUN mkdir -p /save && chmod 777 /save

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY zork_bot.py .

ENV TERM=xterm

CMD ["python", "zork_bot.py"]
