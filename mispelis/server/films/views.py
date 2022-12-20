from django.shortcuts import render

# Create your views here.
from rest_framework import (viewsets, filters, status, views, authentication, permissions)
from .models import Film, FilmGenre,FilmUser
from .serializers import (FilmSerializer, FilmGenreSerializer,FilmUserSerializer)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ExtendedPagination(PageNumberPagination):
    page_size = 8
    def get_paginated_response(self, data):
        next_link = self.get_next_link()
        previous_link = self.get_previous_link()
        if next_link:
            next_link = next_link.split('/')[-1]
        if previous_link:
            previous_link = previous_link.split('/')[-1]
        return Response({
        'count': self.page.paginator.count,
        'num_pages': self.page.paginator.num_pages,
        'page_number': self.page.number,
        'page_size': self.page_size,
        'next_link': next_link,
        'previous_link': previous_link,
        'results': data
        })
class FilmViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Film.objects.all()
    serializer_class = FilmSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {'year': ['lte', 'gte'],'genres': ['exact']}
    search_fields = ['title', 'year', 'genres__name']
    ordering_fields = ['title', 'year','genres__name', 'favorites', 'average_note']
    pagination_class = ExtendedPagination
    pagination_class.page_size = 8

class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FilmGenre.objects.all()
    serializer_class = FilmGenreSerializer
    lookup_field = 'slug'

class FilmUserViewSet(views.APIView):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        queryset = FilmUser.objects.filter(user=self.request.user)
        serializer = FilmUserSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        try:
            film = Film.objects.get(id=request.data['uuid'])
        except Film.DoesNotExist:
            return Response({'status': 'Film not found'},status=status.HTTP_404_NOT_FOUND)
        film_user, created = FilmUser.objects.get_or_create(user=request.user, film=film)
        # Configuramos cada campo
        film_user.state = request.data.get('state', 0)
        film_user.favorite = request.data.get('favorite', False)
        film_user.note = request.data.get('note', -1)
        film_user.review = request.data.get('review', None)

        if int(film_user.state) == 0:
            film_user.delete()
            return Response({'status': 'Deleted'}, status=status.HTTP_200_OK)
        # En otro caso guardamos los campos de la película de usuario
        else:
            film_user.save()
        return Response({'status': 'Saved'}, status=status.HTTP_200_OK)