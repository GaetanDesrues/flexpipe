FROM python:3.9

RUN useradd -m appuser
WORKDIR /workdir

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./flexpipe /workdir/flexpipe
COPY ./main.py /workdir/main.py
RUN chown -R appuser:appuser /workdir

USER appuser
CMD ["python", main.py]
