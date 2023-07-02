from django.urls import path, include
from rest_framework.routers import DefaultRouter
from watchlist_app.api import views


router = DefaultRouter()
router.register('stream', views.StreamPlatformVS, basename='streamplatform')
router.register('watchlist', views.WatchListViewSet, basename="movie")
# router.register('genericapiview', views.WatchListGenericAPIView,
#                 basename="movie-generic-view")


urlpatterns = [
    path('', views.WatchListAV.as_view(), name='movie-list'),
    path('<int:pk>/', views.WatchDetailAV.as_view(), name='movie-detail'),


    path('', include(router.urls)),

    path('<int:pk>/reviews/create/',
         views.ReviewCreate.as_view(), name='review-create'),
    path('<int:pk>/reviews/', views.ReviewList.as_view(), name='review-list'),
    path('reviews/<int:pk>/', views.ReviewDetail.as_view(), name='review-detail'),

    path('user-reviews/', views.UserReview.as_view(), name='user-review-detail'),

    # GENERIC VIEWS URL
    path('watchlist-generic-api-view/', views.WatchListGenericAPIView.as_view(),
         name='watchlist-generic-api-view'),
    path('watchlist-detail-generic-api-view/<int:pk>/', views.WatchlistDetailGenericAPIView.as_view(),
         name='watchlist-detail-generic-api-view'),

    path('watchlist-list-create-api-view/', views.WatchListListCreateAPIView.as_view(),
         name='watchlist-list-create-api-view'),
    path('watchlist-detail-retrieve-update-destroy-api-view/<int:pk>/', views.WatchlistDetailListCreateDestroyAPIView.as_view(),
         name='watchlist-detail-retrieve-update-destroy-api-view'),


]
