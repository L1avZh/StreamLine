# Runs the StreamLine server only. The client is an interactive TTY
# application and is not meant to run in a container.
FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml README.md ./
COPY streamline ./streamline
RUN pip install --no-cache-dir --no-compile .

FROM python:3.12-slim
RUN useradd --create-home --uid 1000 streamline
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin/streamline /usr/local/bin/streamline
USER streamline
WORKDIR /home/streamline
EXPOSE 54140
ENTRYPOINT ["streamline", "server", "--host", "0.0.0.0", "--port", "54140"]
