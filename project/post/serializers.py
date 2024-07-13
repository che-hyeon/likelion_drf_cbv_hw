from rest_framework import serializers
from .models import *

class PostSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    writer = serializers.CharField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at =serializers.CharField(read_only=True)

    comments = serializers.SerializerMethodField(read_only=True)
    def get_comments(self, instance):
        serializer = CommentSerializer(instance.comments, many=True)
        return serializer.data
    
    like = serializers.SerializerMethodField(read_only=True)
    def get_like(self, instance):
        likes = instance.like.all()
        return [like.username for like in likes]
    
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = [
            "id",
            "writer",
            "created_at",
            "updated_at",
            "like_num"
        ]

    image = serializers.ImageField(use_url = True, required=False)

class CommentSerializer(serializers.ModelSerializer):
    post = serializers.SerializerMethodField(read_only = True)
    def get_post(self, instance):
        post = instance.post
        return post.title
    
    writer = serializers.SerializerMethodField(read_only = True)
    def get_writer(self, instance):
        return instance.writer.username
    
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['post', 'writer']