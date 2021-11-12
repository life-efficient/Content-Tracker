FROM python:3.8

COPY slack.py /slack.py

RUN python -m pip install --upgrade pip \
    pip install slack-sdk PyGithub

ENTRYPOINT ["python", "/slack.py"]