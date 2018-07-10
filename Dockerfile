FROM        python:3-slim
ENV         PYTHONUNBUFFERED=true
RUN         useradd -m -U app && \
            chown -R app:app /home/app && \
            pip install boto3 stomp.py wait
USER        app
WORKDIR     /home/app/current
RUN         mkdir -p /home/app/.aws && \
            touch /home/app/.aws/config
COPY        . /home/app/current
CMD         ./fcrepo_sns.py
HEALTHCHECK --start-period=5s CMD true
