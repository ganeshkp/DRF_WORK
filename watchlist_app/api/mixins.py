
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

# https://stackoverflow.com/questions/70738517/drf-creating-mixin-using-different-serializers-objects


# class MultipleFieldLookupMixin:
#     """
#     Apply this mixin to any view or viewset to get multiple field filtering
#     based on a `lookup_fields` attribute, instead of the default single field filtering.
#     """

#     def get_object(self):
#         queryset = self.get_queryset()             # Get the base queryset
#         queryset = self.filter_queryset(queryset)  # Apply any filter backends
#         filter = {}
#         for field in self.lookup_fields:
#             if self.kwargs.get(field):  # Ignore empty fields.
#                 filter[field] = self.kwargs[field]
#         obj = get_object_or_404(queryset, **filter)  # Lookup the object
#         self.check_object_permissions(self.request, obj)
#         return obj


class CustomMixin:
    serializer_class = None
    model_class = None

    def get(self, request, recipe_id):
        user = request.user.id
        data = {"user": user, "recipe": recipe_id}
        serializer = self.serializer_class(
            data=data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        user = request.user
        obj = get_object_or_404(
            self.model_class, user=user, recipe__id=recipe_id
        )
        obj.delete()
        return Response(
            "Рецепт удален из избранного", status.HTTP_204_NO_CONTENT
        )


# Usage of mixin is as below
# class FavoriteViewSet(CustomMixin, APIView):
#     serializer_class = FavoriteSerializer
#     model_class = Favorite


# class PurchaseListView(CustomMixin, APIView):
#     serializer_class = PurchaseListSerializer
#     model_class = PurchaseList
