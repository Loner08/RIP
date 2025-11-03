from django.urls import path

from .views import *

urlpatterns = [
    path('', index),
    path('consumers/<int:consumer_id>/', consumer_page, name="consumer_page"),
    path('reserves/<int:reserve_id>/', reserve_page, name="reserve_page"),
    path('consumers/<int:consumer_id>/add_to_reserve/', add_consumer_to_draft_reserve,
         name="add_consumer_to_draft_reserve"),
    path('reserves/<int:reserve_id>/delete/', delete_reserve, name="delete_reserve")
]
