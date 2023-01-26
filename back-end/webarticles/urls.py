from django.urls import path
from webarticles import views

urlpatterns = [
    path('wsjlist/', views.WsjList.as_view()),
    path('nytlist/', views.NytList.as_view()),
    path('wsj/', views.wall_street_journal),
    path('nyt/', views.new_york_times),
]