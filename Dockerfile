FROM python:3.12-slim

WORKDIR /app
COPY scripts/stripe_managed_payments.py /app/scripts/stripe_managed_payments.py
COPY pipeline/stripe_catalog.json /app/pipeline/stripe_catalog.json
COPY docs/success.html /app/docs/success.html
COPY docs/cancel.html /app/docs/cancel.html

ENV HOST=0.0.0.0
EXPOSE 4242

CMD ["python3", "scripts/stripe_managed_payments.py", "serve", "--host", "0.0.0.0"]
