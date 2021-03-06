from django.contrib import admin
from django.urls import path
from .views import ItemList, ItemDetail, ItemCreate, ItemDelete, ItemUpdate

urlpatterns = [
    path('', ItemList.as_view(), name='item.list'),
    path('<int:pk>/', ItemDetail.as_view(), name='item.detail'),
    path('create/', ItemCreate.as_view(), name='item.create'),
    path('delete/<int:pk>/', ItemDelete.as_view(), name='item.delete'),
    path('update/<int:pk>/', ItemUpdate.as_view(), name='item.update'),
]
