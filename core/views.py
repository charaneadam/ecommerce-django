from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, View
from django.utils import timezone
from django.contrib import messages
from .models import Item, OrderItem, Order, BillingAddress, Payment
from .forms import CheckoutForm


import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY



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
            return redirect('core:home')
        return render(self.request, 'order-summary.html', context)

class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'

class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form': form,
        }
        return render(self.request, 'checkout-page.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # TODO: add functionalities to these fields
                # same_billing_address = form.cleaned_data.get('same_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                # TODO: add redirect to the selected payment option
                return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.error(self.request ,"You do not have an active order.")
            return redirect('core:order-summary')

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

class PaymentView(View):
    def get(self, *args, **kwargs):
        # order
        return render(self.request, 'payment.html')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        amount = int(order.get_total_price() * 100) # x100 since it's in cents
        token = self.request.POST.get('stripeToken')

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token,
            )

            # Create the payment
            payment = Payment()
            payment.stripe_charge_id = charge.id
            payment.user = self.request.user
            payment.amount = amount
            payment.save()

            # Assign the payment to the order
            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Your order was successful.")
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught

            messages.error(self.request, f'{e.error.message}')

            print('Status is: %s' % e.http_status)
            print('Type is: %s' % e.error.type)
            print('Code is: %s' % e.error.code)
            # param is '' in this case
            print('Param is: %s' % e.error.param)
            print('Message is: %s' % e.error.message)
        except stripe.error.RateLimitError as e:
            messages.error(self.request, "Rate limit error.")
        except stripe.error.InvalidRequestError as e:
            messages.error(self.request, "Invalid parameters.")
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Authentication error.")
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Network error.")
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong. You were not charged. Please try again.")
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            # Send email to admin
            messages.error(self.request, "A system error occured. We have been notified.")
        finally:
            return redirect('core:home')

@login_required()
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