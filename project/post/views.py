from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response

from .models import Post, Comment
from . serializers import PostSerializer, CommentSerializer

from rest_framework.permissions import IsAuthenticatedOrReadOnly

from rest_framework.decorators import action

# Create your views here.
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # 이거 뭔지 잘 모르겠음... 왜 perform_create를 rewriting 해줘야함?
    def perform_create(self, serializer):
        serializer.save(writer=self.request.user)

    @action(methods=["POST"], detail=True)
    def likes(self, request, pk=None):
        like_movie = self.get_object()
        if request.user in like_movie.like.all():
            like_movie.like.remove(request.user)
            like_movie.like_num -= 1
            like_movie.save()
        else:
            like_movie.like.add(request.user)
            like_movie.like_num += 1
            like_movie.save()
        return Response()
    
    @action(methods=["GET"], detail=False)
    def like_rank(self, request):
        rank_post = self.get_queryset().order_by("-like_num")[:3]
        rank_post_serializer = PostSerializer(rank_post, many=True)
        return Response(rank_post_serializer.data)

class CommentViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

class PostCommentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

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