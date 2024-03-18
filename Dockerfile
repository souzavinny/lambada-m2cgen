FROM --platform=linux/riscv64 ghcr.io/stskeeps/python:3.10-slim-jammy-estargz
ENV PATH="/opt/cartesi/bin:${PATH}"

WORKDIR /opt/cartesi/dapp
COPY ./requirements.txt .

RUN <<EOF
pip install -r requirements.txt --no-cache
find /usr/local/lib -type d -name __pycache__ -exec rm -r {} +
EOF

COPY ./dapp.py .

ENV ROLLUP_HTTP_SERVER_URL="http://127.0.0.1:5004"

CMD ["python3", "dapp.py"]