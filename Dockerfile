FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system app && adduser --system --ingroup app appuser

COPY --chown=appuser:app . .

RUN mkdir -p /app/instance /app/app/database \
    && chown -R appuser:app /app

EXPOSE 5000

USER appuser

CMD ["python", "run.py"]
