from django.urls import path
from catalog import views
urlpatterns = [path("", views.index), path("export/<str:kind>/", views.export)]
