FROM python:3.10 as base

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash app
WORKDIR /home/app

ENV PYTHONUNBUFFERED=1

RUN chown -R app:app /home/app

ADD requirements.txt .
ADD colors.txt .
ADD usernames.txt .

RUN pip install --no-cache-dir -r requirements.txt

USER app

FROM base as final
ADD . .

CMD ["python3", "entrypoint.py"]
