FROM ubuntu:20.04
WORKDIR /WordMp3Scraper

RUN apt-get update && apt-get install -y python3.6 python3-distutils python3-pip python3-apt
RUN python3 -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install --upgrade -r requirements.txt
EXPOSE 1337
COPY . .
CMD [ "flask", "run", "--host=0.0.0.0" ]