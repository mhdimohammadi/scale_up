for testing you can run the python manage.py test inside the container.
also remember to run python manage.py makemigrations and migrate in the container so the tables are created.
for building image using the dockerfile and docker-compose please and 'HOST': 'db' to the DATABASES in the settings.py 
it should look like this :
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': 'db',
        'PORT': os.getenv('PORT'),
    }
}
```
git hub : https://github.com/mhdimohammadi/scale_up
