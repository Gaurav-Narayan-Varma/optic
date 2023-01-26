from django.db import models

# tables with the latest data
class WsjArticle(models.Model):
    title = models.CharField(max_length=100)
    link = models.CharField(max_length=200)
    entity = models.CharField(max_length=200)
    full = models.CharField(max_length=200)
    
class NytArticle(models.Model):
    title = models.CharField(max_length=100)
    link = models.CharField(max_length=200)
    entity = models.CharField(max_length=200)
    full = models.CharField(max_length=200)

# stable tables which only update when the latest data table is fully updated
class WsjStable(models.Model):
    title = models.CharField(max_length=100)
    link = models.CharField(max_length=200)
    entity = models.CharField(max_length=200)
    full = models.CharField(max_length=200)
    
class NytStable(models.Model):
    title = models.CharField(max_length=100)
    link = models.CharField(max_length=200)
    entity = models.CharField(max_length=200)
    full = models.CharField(max_length=200)