remember to run python manage.py makemigrations and migrate in the container so the tables are created.
for building image using the dockerfile and docker-compose please change the host to 'HOST': 'db' in the DATABASES in 
the settings.py, it should look like this :
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
urls :
 ```
 urlpatterns = [
    path('flags/',views.FlagListView.as_view(),name='flag_list'), #GET
    path('flags/<int:pk>',views.FlagDetailView.as_view(),name='flag_detail'), #GET
    path('toggle/<int:pk>',views.FlagToggleView.as_view(),name='flag_toggle'), #POST
    path('add_flag',views.AddFlagView.as_view(),name='add_flag'), #POST
    path('add_dependency',views.AddDependencyView.as_view(),name='add_dependency'), #POST
    path('logs',views.AuditLogListView.as_view(),name='logs'), #GET
]
 ```