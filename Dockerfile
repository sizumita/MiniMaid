FROM python:3.8

RUN apt-get update && \
    apt-get install -y \
    opus-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /bot

COPY requirements.txt /bot

RUN pip install -r requirements.txt

COPY bot.py /bot
COPY main.py /bot
COPY cogs /bot/cogs

CMD ["python", "main.py"]
