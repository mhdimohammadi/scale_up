from django.urls import path
from . import views



app_name = "flag"
urlpatterns = [
    path('flags/',views.FlagListView.as_view(),name='flag_list'),
    path('flags/<int:pk>',views.FlagDetailView.as_view(),name='flag_detail'),
    path('toggle/<int:pk>',views.FlagToggleView.as_view(),name='flag_toggle'),
    path('add_flag',views.AddFlagView.as_view(),name='add_flag'),
    path('add_dependency',views.AddDependencyView.as_view(),name='add_dependency'),
    path('logs',views.AuditLogListView.as_view(),name='logs'),
]