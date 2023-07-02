from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from rest_framework import filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.parsers import JSONParser, FormParser
from rest_framework.decorators import parser_classes
from rest_framework import filters, generics, status, viewsets, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework.decorators import action

from watchlist_app.api import pagination, permissions, serializers, throttling
from watchlist_app.models import Review, StreamPlatform, WatchList


class UserReview(generics.ListAPIView):
    serializer_class = serializers.ReviewSerializer
    search_fields = ['username', 'email']
    filter_backends = [filters.SearchFilter]
    ordering_fields = ['username', 'email']

    def get_queryset(self):
        username = self.request.query_params.get('username', None)
        return Review.objects.filter(review_user__username=username)


class ReviewCreate(generics.CreateAPIView):
    serializer_class = serializers.ReviewSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [throttling.ReviewCreateThrottle]

    def get_queryset(self):
        return Review.objects.all()

    def perform_create(self, serializer):
        pk = self.kwargs.get('pk')
        watchlist = WatchList.objects.get(pk=pk)

        review_user = self.request.user
        review_queryset = Review.objects.filter(
            watchlist=watchlist, review_user=review_user)

        if review_queryset.exists():
            raise ValidationError("You have already reviewed this movie!")

        if watchlist.number_rating == 0:
            watchlist.avg_rating = serializer.validated_data['rating']
        else:
            watchlist.avg_rating = (
                watchlist.avg_rating + serializer.validated_data['rating'])/2

        watchlist.number_rating = watchlist.number_rating + 1
        watchlist.save()

        serializer.save(watchlist=watchlist, review_user=review_user)


class ReviewList(generics.ListAPIView):
    serializer_class = serializers.ReviewSerializer
    throttle_classes = [throttling.ReviewListThrottle, AnonRateThrottle]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['review_user__username', 'active']

    def get_queryset(self):
        pk = self.kwargs['pk']
        return Review.objects.filter(watchlist=pk)


class ReviewDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = serializers.ReviewSerializer
    permission_classes = [permissions.IsReviewUserOrReadOnly]
    throttle_classes = [ScopedRateThrottle, AnonRateThrottle]
    throttle_scope = 'review-detail'


class StreamPlatformVS(viewsets.ModelViewSet):
    queryset = StreamPlatform.objects.all()
    serializer_class = serializers.StreamPlatformSerializer
    permission_classes = [permissions.IsAdminOrReadOnly]
    throttle_classes = [AnonRateThrottle]


class WatchListAV(APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle]
    renderer_classes = (JSONRenderer, )
    # parser_classes = [JSONParser, FormParser]

    @method_decorator(cache_page(60*60*2))
    @method_decorator(vary_on_headers("Authorization",))
    @method_decorator(vary_on_cookie)
    def get(self, request, format=None):
        movies = WatchList.objects.all()
        serializer = serializers.WatchListSerializer(movies, many=True)
        return Response(serializer.data)

    @parser_classes([JSONParser])
    def post(self, request):
        serializer = serializers.WatchListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    @parser_classes([FormParser])
    def put(self, request):
        # Your code for PUT method
        pass

    # you can override the get_renderers() method in your view class to dynamically determine the rendering classes for a particular view based on the request.
    # def get_renderers(self):
    #     if self.request.accepted_renderer.format == 'html':
    #         return [TemplateHTMLRenderer()]
    #     else:
    #         return [JSONRenderer()]

    # you can override the get_parsers() method in your view class to dynamically determine the parsing classes for a particular view based on the request.
    # def get_parsers(self):
    #     if self.request.content_type == 'application/x-www-form-urlencoded':
    #         return [FormParser()]
    #     else:
    #         return [JSONParser()]


class WatchlistDetailGenericAPIView(mixins.RetrieveModelMixin,
                                    mixins.UpdateModelMixin,
                                    mixins.DestroyModelMixin,
                                    generics.GenericAPIView):
    queryset = WatchList.objects.all()
    serializer_class = serializers.WatchListSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class WatchlistDetailListCreateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WatchList.objects.all()
    serializer_class = serializers.WatchListSerializer


class WatchDetailAV(APIView):
    permission_classes = [permissions.IsAdminOrReadOnly]
    throttle_classes = [AnonRateThrottle]

    def get(self, request, pk):
        try:
            movie = WatchList.objects.get(pk=pk)
        except WatchList.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.WatchListSerializer(movie)
        return Response(serializer.data)

    def put(self, request, pk):
        movie = WatchList.objects.get(pk=pk)
        serializer = serializers.WatchListSerializer(movie, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        movie = WatchList.objects.get(pk=pk)
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WatchListGenericAPIView(mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              generics.GenericAPIView):

    queryset = WatchList.objects.all()
    serializer_class = serializers.WatchListSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class WatchListListCreateAPIView(generics.ListCreateAPIView):
    queryset = WatchList.objects.all()
    serializer_class = serializers.WatchListSerializer


class WatchListViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, )
    renderer_classes = (JSONRenderer, )
    queryset = WatchList.objects.all()
    serializer_class = serializers.WatchListSerializer
    filter_fields = ('title', 'platform')
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle]

    def get_queryset(self):
        # GET only the objects from platform 1
        return WatchList.objects.filter(platform='1')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        instance = self.get_object()
        # Perform custom logic on the instance
        # ...
        if instance.avg_rating < 4.0:
            instance.avg_rating = 4.0
            instance.save()
        return Response({'message': 'Custom action executed'})
