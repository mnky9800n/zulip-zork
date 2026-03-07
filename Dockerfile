FROM clockworksoul/zork1 AS game

FROM python:3.12-bookworm

# Install frotz (the interactive fiction interpreter)
RUN apt-get update && apt-get install -y --no-install-recommends \
    frotz \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Copy game data from the zork1 image
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
