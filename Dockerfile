FROM python:3.8
#FROM ubuntu:18.04 as builder

WORKDIR /var/speech

RUN apt-get update && \
    apt-get install -y build-essential cmake git libasound-dev

RUN git clone https://github.com/sizumita/jtalkdll.git

WORKDIR /var/speech/jtalkdll

RUN bash build

#COPY --from=builder /usr/local/lib/libjtalk.so /usr/local/lib
#COPY --from=builder /usr/local/include/jtalk.h /usr/local/include
#COPY --from=builder /usr/local/OpenJTalk/dic_utf_8 /usr/local/OpenJTalk/dic_utf_8
#COPY --from=builder /usr/local/OpenJTalk/voice /usr/local/OpenJTalk/voice


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
COPY lib /bot/lib
COPY dic.json /bot

CMD ["python", "main.py"]
