

FROM python:3.14-slim

WORKDIR /app      
#Makes the relative path to be used as the working directory

COPY requirements.txt . 
#Copies dependencies from laptop to /app 

RUN pip install --no-cache-dir -r requirements.txt
 #installs flask app and dependencies in the container

COPY . . 
# Copies everything from folder into WORKDIR /app


CMD ["python", "app.py"] 
#The container runs the app

EXPOSE 5000