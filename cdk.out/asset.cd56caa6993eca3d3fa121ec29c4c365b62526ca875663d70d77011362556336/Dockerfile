FROM public.ecr.aws/lambda/python:3.7

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN yum install -y gcc gcc-c++ make

RUN yum install -y mesa-libGL

RUN pip install -r requirements.txt

COPY src/* ${LAMBDA_TASK_ROOT}

CMD ["main.handler"]
