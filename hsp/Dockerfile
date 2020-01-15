FROM python:3.6

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

WORKDIR /usr/src/app/
CMD ["python", "hsp.py"]
