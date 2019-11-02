from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, View
from django.utils import timezone
from django.contrib import messages
from .models import Item, OrderItem, Order


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = 'home-page.html'

class OrderItemView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'object': order}
        except ObjectDoesNotExist:
            messages.error(self.request ,"You do not have an active order.")
            return redirect('/')
        return render(self.request, 'order-summary.html', context)

class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'

def checkout(request):
    return render(request, 'checkout-page.html')

@login_required()
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
    return redirect("core:order-summary")

def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            # add a message that the user doesnt have an order
            messages.info(request, "This item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        # add a message that the user doesnt have an order
        messages.warning(request, "You do not have an order.")
        return redirect("core:product", slug=slug)


@login_required()
def remove_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            # add a message that the user doesnt have an order
            messages.info(request, "This item was not in your cart.")
            return redirect("core:order-summary", slug=slug)
    else:
        # add a message that the user doesnt have an order
        messages.warning(request, "You do not have an order.")
        return redirect("core:product", slug=slug)