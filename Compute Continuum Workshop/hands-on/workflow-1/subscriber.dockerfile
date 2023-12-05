FROM python:3.8

WORKDIR /home

RUN apt update 

RUN pip install paho-mqtt

COPY subscriber.py /home/

ENV PYTHONUNBUFFERED=1

# Shrink image size
RUN rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["python3"]
CMD ["subscriber.py"]

