FROM python:3.9

ENV PYTHONUNBUFFERED=1

# Copy only requirements to cache them in docker layer
WORKDIR /code

RUN pip install --upgrade pip
COPY requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt

# Creating folders, and files for a project:
COPY . /code

EXPOSE 8000

CMD python manage.py runserver 0.0.0.0:8000