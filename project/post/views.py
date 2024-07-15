from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response

from .models import Post, Comment, Tag
from . serializers import PostSerializer, CommentSerializer, TagSerializer

from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from .permissions import IsOwnerOrReadOnly

from rest_framework.decorators import action

# Create your views here.
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_permissions(self):
        if self.action in ["update", "destroy", "partial_update"]:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        post = serializer.instance
        self.handle_tags(post)

        return Response(serializer.data)

    # 이거 뭔지 잘 모르겠음... 왜 perform_create를 해줘야함?
    def perform_create(self, serializer):
        serializer.save(writer=self.request.user)
        post = serializer.save()
        post.tag.clear()
        self.handle_tags(post)
    
    def perform_update(self, serializer):
        serializer.save(writer=self.request.user)
        post = serializer.save()
        post.tag.clear()
        self.handle_tags(post)

    def handle_tags(self, post):
        tags = [word[1:] for word in post.content.split(' ') if word.startswith('#')]
        for t in tags:
            tag, created = Tag.objects.get_or_create(name=t)
            post.tag.add(tag)
        post.save()

    @action(methods=["POST"], detail=True)
    def likes(self, request, pk=None):
        like_post = self.get_object()
        if request.user in like_post.like.all():
            like_post.like.remove(request.user)
            like_post.like_num -= 1
            like_post.save()
        else:
            like_post.like.add(request.user)
            like_post.like_num += 1
            like_post.save()
        return Response()
    
    @action(methods=["GET"], detail=False)
    def like_rank(self, request):
        rank_post = self.get_queryset().order_by("-like_num")[:3]
        rank_post_serializer = PostSerializer(rank_post, many=True)
        return Response(rank_post_serializer.data)

class CommentViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.action in ["update", "destroy", "partial_update"]:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]

class PostCommentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def list(self, request, post_id=None):
        post = get_object_or_404(Post, id=post_id)
        queryset = self.filter_queryset(self.get_queryset().filter(post=post))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, post_id=None):
        post = get_object_or_404(Post, id=post_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, writer=self.request.user)
        return Response(serializer.data)

class TagViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "name"
    lookup_url_kwarg = "tag_name"

    def retrieve(self, request, *args, **kwargs):
        tag_name = kwargs.get("tag_name")
        tag = get_object_or_404(Tag, name=tag_name)
        posts = Post.objects.filter(tag=tag)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)