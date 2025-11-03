from django.urls import path
from .views import *

urlpatterns = [
    path('api/consumers/', search_consumers),  # GET
    path('api/consumers/<int:consumer_id>/', get_consumer_by_id),  # GET
    path('api/consumers/<int:consumer_id>/update/', update_consumer),  # PUT
    path('api/consumers/<int:consumer_id>/update_image/', update_consumer_image),  # POST
    path('api/consumers/<int:consumer_id>/delete/', delete_consumer),  # DELETE
    path('api/consumers/create/', create_consumer),  # POST
    path('api/consumers/<int:consumer_id>/add_to_reserve/', add_consumer_to_reserve),  # POST

    path('api/reserves/', search_reserves),  # GET
    path('api/reserves/cart/', get_cart_info),  # GET
    path('api/reserves/<int:reserve_id>/', get_reserve_by_id),  # GET
    path('api/reserves/<int:reserve_id>/update/', update_reserve),  # PUT
    path('api/reserves/<int:reserve_id>/update_status_user/', update_status_user),  # PUT
    path('api/reserves/<int:reserve_id>/update_status_admin/', update_status_admin),  # PUT
    path('api/reserves/<int:reserve_id>/delete/', delete_reserve),  # DELETE

    path('api/reserves/<int:reserve_id>/update_consumer/<int:consumer_id>/', update_consumer_in_reserve),  # PUT
    path('api/reserves/<int:reserve_id>/delete_consumer/<int:consumer_id>/', delete_consumer_from_reserve),  # DELETE

    path('api/users/register/', register), # POST
    path('api/users/update/', update_user), # PUT
    path("api/users/info/", user_info), # GET
    path('api/users/login/', login), # POST
    path('api/users/logout/', logout), # POST
]
