"""
Internal Django Database Reset Script for pretix.
Purges transient orders, positions, payments, and cart entries for event 'sqe2026',
and restores quota availability to baseline state (size: 10, available: 10).
"""
import os
import sys
from decimal import Decimal
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pretix.settings')
django.setup()

from django_scopes import scope
from pretix.base.models import (
    Organizer, Event, Item, Quota, Order, OrderPosition, CartPosition,
    OrderFee, OrderPayment, OrderRefund, Invoice
)
from pretix.base.models.orders import Transaction
from pretix.base.models.giftcards import GiftCardTransaction

print("[RESET] Initiating pretix database reset to baseline state...")

try:
    org = Organizer.objects.get(slug='sqe')
except Organizer.DoesNotExist:
    print("[RESET_ERROR] Organizer 'sqe' does not exist. Run seed first.")
    sys.exit(1)

with scope(organizer=org):
    try:
        event = Event.objects.get(organizer=org, slug='sqe2026')
    except Event.DoesNotExist:
        print("[RESET_ERROR] Event 'sqe2026' does not exist. Run seed first.")
        sys.exit(1)

    # 1. Cascade purge protected dependent models in strict FK dependency order
    tx_del, _ = Transaction.objects.filter(order__event=event).delete()
    gc_del, _ = GiftCardTransaction.objects.filter(order__event=event).delete()
    inv_del, _ = Invoice.objects.filter(order__event=event).delete()
    ref_del, _ = OrderRefund.objects.filter(order__event=event).delete()
    pay_del, _ = OrderPayment.objects.filter(order__event=event).delete()
    fee_del, _ = OrderFee.objects.filter(order__event=event).delete()
    pos_del, _ = OrderPosition.objects.filter(order__event=event).delete()
    cart_del, _ = CartPosition.objects.filter(event=event).delete()
    
    # 2. Purge orders
    orders_deleted, _ = Order.objects.filter(event=event).delete()

    # 3. Reset Quota to baseline capacity 10
    quota = Quota.objects.get(event=event, name='General Admission Quota')
    quota.size = 10
    quota.save()

    # 4. Ensure Item is active and default price is €50.00
    item = Item.objects.get(event=event, default_price=Decimal('50.00'))
    item.active = True
    item.save()
    quota.items.set([item])

    # 5. Invariant Verification
    remaining_orders = Order.objects.filter(event=event).count()
    remaining_positions = OrderPosition.objects.filter(order__event=event).count()
    avail_status, avail_num = quota.availability()

    print(f"[RESET] Purged {orders_deleted} orders, {pos_del} positions, {tx_del} transactions, {cart_del} cart items.")
    print(f"[RESET] Invariant Check: Remaining Orders={remaining_orders}, Quota Size={quota.size}, Available={avail_num}, Status={avail_status}")

    if remaining_orders == 0 and avail_num == 10:
        print(f"RESET_SUCCESS:ORDERS={remaining_orders}:QUOTA_AVAILABILITY={avail_num}:QUOTA_SIZE={quota.size}")
        sys.exit(0)
    else:
        print(f"[RESET_ERROR] Invariants violated! Orders={remaining_orders}, Avail={avail_num}")
        sys.exit(2)
