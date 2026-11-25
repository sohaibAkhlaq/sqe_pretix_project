"""Scoped pretix server-side business logic under white-box verification.

Every method/function body below is verbatim from pinned pretix v2026.9.3
(commit db000dc2986ff595eb3fe4703c4a46c5fe180abe) and is AST-verified by
tests/team/unit/production_source.py (`assert_ast_matches_upstream`):
- BR1: OrderChangeManager._check_quotas (services/orders.py:2285-2294)
- BR2: QuotaAvailability._compute_early_outs (services/quotas.py:493-500)
- BR3: Order.cancel_allowed (models/orders.py:646-649) & mark_order_expired (services/orders.py:360-382)
- BR4: Order._can_be_paid (models/orders.py:1026-1047)
"""
from typing import Union

_ = None
OrderError = None
QuotaAvailability = None
User = None
transaction = None
generate_cancellation = None
order_expired = None
time_machine_now = None


class Quota:
    AVAILABILITY_OK = 100
    AVAILABILITY_GONE = 20
    AVAILABILITY_ORDERED = 0


class QuotaAvailabilityPolicy:
    def _compute_early_outs(self, quotas):
        for q in quotas:
            if q.closed and not self._ignore_closed:
                self.results[q] = Quota.AVAILABILITY_ORDERED, 0
            elif q.size is None:
                self.results[q] = Quota.AVAILABILITY_OK, None
            elif q.size == 0:
                self.results[q] = Quota.AVAILABILITY_GONE, 0


class OrderChangeManager:
    def _check_quotas(self):
        qa = QuotaAvailability()
        qa.queue(*[k for k, v in self._quotadiff.items() if v > 0])
        qa.compute()
        for quota, diff in self._quotadiff.items():
            if diff <= 0:
                continue
            avail = qa.results[quota]
            if avail[0] != Quota.AVAILABILITY_OK or (avail[1] is not None and avail[1] < diff):
                raise OrderError(self.error_messages['quota'].format(name=quota.name))


class Order:
    STATUS_PENDING = "n"
    STATUS_PAID = "p"
    STATUS_EXPIRED = "e"
    STATUS_CANCELED = "c"
    objects = None

    def cancel_allowed(self):
        return (
            self.status in (Order.STATUS_PENDING, Order.STATUS_PAID, Order.STATUS_EXPIRED) and self.count_positions
        )

    def _can_be_paid(self, count_waitinglist=True, ignore_date=False, force=False, lock=False) -> Union[bool, str]:
        error_messages = {
            'late_lastdate': _("The payment can not be accepted as the last date of payments configured in the "
                               "payment settings is over."),
            'late': _("The payment can not be accepted as the order is expired and you configured that no late "
                      "payments should be accepted in the payment settings."),
            'require_approval': _('This order is not yet approved by the event organizer.')
        }
        if not force:
            if self.require_approval:
                return error_messages['require_approval']
            term_last = self.payment_term_last
            if term_last and not ignore_date:
                if time_machine_now() > term_last:
                    return error_messages['late_lastdate']

        if self.status == self.STATUS_PENDING:
            return True
        if not self.event.settings.get('payment_term_accept_late') and not ignore_date and not force:
            return error_messages['late']

        return self._is_still_available(count_waitinglist=count_waitinglist, force=force, lock=lock)


def mark_order_expired(order, user=None, auth=None):
    """
    Mark this order as expired. This sets the order status, generates an invoice cancellation
    and returns the order object.
    :param order: The order to change
    :param user: The user that performed the change
    """
    with transaction.atomic():
        if isinstance(order, int):
            order = Order.objects.get(pk=order)
        if isinstance(user, int):
            user = User.objects.get(pk=user)
        order.status = Order.STATUS_EXPIRED
        order.save(update_fields=['status'])

        order.log_action('pretix.event.order.expired', user=user, auth=auth)
        i = order.invoices.filter(is_cancellation=False).last()
        if i and not i.refered.exists():
            generate_cancellation(i)
        order.create_transactions()

    order_expired.send(order.event, order=order)
    return order
