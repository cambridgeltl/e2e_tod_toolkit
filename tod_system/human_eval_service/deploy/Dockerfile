FROM mortals/codeenv:conda-cuda12.0

RUN apt update -y && apt install build-essential
WORKDIR /root/tod_system

COPY . .

ENV PYTHONPATH=$(pwd)

RUN python download_data.py

RUN pip install -r requirement.txt
