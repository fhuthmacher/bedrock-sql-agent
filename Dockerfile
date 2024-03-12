FROM amazon/aws-lambda-python:3.11

RUN mkdir -p /opt

# Install deps
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY index.py ${LAMBDA_TASK_ROOT}
COPY tools.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "index.handler" ]