FROM python:3.7
LABEL Alex Anderson
COPY . /discord-queue-bot
WORKDIR /discord-queue-bot
RUN pip install -r ./requirements.txt
EXPOSE 443
CMD python ./bot.py
