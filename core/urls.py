from django.urls import path
from .views import (
    HomeView,
    CheckoutView,
    ItemDetailView,
    OrderItemView,
    PaymentView,
    add_to_cart,
    remove_from_cart,
    remove_item_from_cart
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('order-summary/', OrderItemView.as_view(), name='order-summary'),
    path('remove-item-from-cart/<slug>', remove_item_from_cart, name='remove-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment')
]
