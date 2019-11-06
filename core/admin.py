from django.contrib import admin

from .models import Item, OrderItem, Order, Payment, Coupon, Refund

def accept_refund(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)

accept_refund.short_description = 'Update orders to refund granted'

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered', 'delivered', 'received', 'refund_requested', 'refund_granted', 'billing_address', 'payment', 'coupon']
    list_filter = ['ordered', 'delivered', 'received', 'refund_requested', 'refund_granted']
    list_display_links = ['billing_address', 'payment', 'coupon']
    search_fields = ['user__username', 'ref_code']
    actions = [accept_refund]

admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)