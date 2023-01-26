from rest_framework import serializers
from webarticles.models import WsjArticle, NytArticle, WsjStable, NytStable
from webarticles.models import NytArticle

class WsjSerializer(serializers.ModelSerializer):
    class Meta:
        model = WsjArticle
        fields = ['id', 'title', 'link', 'entity', 'full']
        
class NytSerializer(serializers.ModelSerializer):
    class Meta:
        model = NytArticle
        fields = ['id', 'title', 'link', 'entity', 'full']
        
class WsjStableSerializer(serializers.ModelSerializer):
    class Meta:
        model = WsjStable
        fields = ['id', 'title', 'link', 'entity', 'full']
        
class NytStableSerializer(serializers.ModelSerializer):
    class Meta:
        model = NytStable
        fields = ['id', 'title', 'link', 'entity', 'full']
