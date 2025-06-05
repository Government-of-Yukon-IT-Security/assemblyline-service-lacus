FROM cccs/assemblyline-v4-service-base:stable

# Python path to the service class from your service directory
#  The following example refers to the class "Sample" from the "result_sample.py" file
ENV SERVICE_PATH=lacus.lacus.Lacus

# Install any service dependencies here
# For example: RUN apt-get update && apt-get install -y libyaml-dev
#
#              COPY requirements.txt requirements.txt
#              RUN pip install --no-cache-dir --user --requirement requirements.txt && rm -rf ~/.cache/pip

# Build dependencies
USER root
RUN apt-get update && apt-get -y install build-essential curl git python3 ffmpeg

RUN mkdir -p /app

WORKDIR /app

# Install Valkey
RUN git clone https://github.com/valkey-io/valkey.git

WORKDIR /app/valkey

RUN git checkout 8.0 && make

WORKDIR /app

# Install lacus
RUN git clone https://github.com/ail-project/lacus.git

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app/lacus

RUN poetry install && poetry run playwright install-deps

RUN echo LACUS_HOME="`pwd`" >> .env

RUN poetry run update --init

RUN apt-get install -y supervisor

WORKDIR /app

COPY ./lacus/entrypoint.sh .
COPY ./lacus/supervisord.conf .
RUN chmod +x entrypoint.sh

RUN chown -R assemblyline:assemblyline /app

# Switch to assemblyline user
USER assemblyline

WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/var/lib/assemblyline/.local/bin/:${PATH}"

WORKDIR /app/lacus
RUN poetry install && poetry run playwright install

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --user --requirement requirements.txt && rm -rf ~/.cache/pip

USER root

WORKDIR /opt/al_service
COPY . .

RUN chown -R assemblyline:assemblyline /opt/al_service

USER assemblyline

ENTRYPOINT ["/app/entrypoint.sh"]
