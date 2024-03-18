# build stage: generates model
FROM python:3.8.10 as model

WORKDIR /usr/src/app
COPY ./model .
RUN pip3 install -r requirements.txt
RUN python3 build_model.py


FROM --platform=linux/riscv64 ghcr.io/stskeeps/python:3.10-slim-jammy-estargz
ENV PATH="/opt/cartesi/bin:${PATH}"

WORKDIR /opt/cartesi/dapp
COPY ./requirements.txt .

RUN <<EOF
pip install -r requirements.txt --no-cache
find /usr/local/lib -type d -name __pycache__ -exec rm -r {} +
EOF

COPY ./m2cgen.py .
COPY --from=model /usr/src/app/model.py .

ENV ROLLUP_HTTP_SERVER_URL="http://127.0.0.1:5004"

CMD ["python3", "m2cgen.py"]