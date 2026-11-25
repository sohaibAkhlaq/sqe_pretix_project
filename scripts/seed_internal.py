"""
Internal Django Seeding Script for Pretix.
Executed inside the pretix Docker container via:
docker exec pretix_web python3 /data/seed_internal.py
"""
import os
import sys
from decimal import Decimal
from datetime import timedelta
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pretix.settings')
django.setup()

from django.utils.timezone import now
from django_scopes import scope
from pretix.base.models import User, Organizer, Event, Item, Quota, Team, TeamAPIToken

print("Starting pretix internal database seed...")

admin_password = os.environ.get('SQE_ADMIN_PASSWORD')
auditor_password = os.environ.get('SQE_AUDITOR_PASSWORD')
if not admin_password or not auditor_password:
    raise SystemExit('SQE_ADMIN_PASSWORD and SQE_AUDITOR_PASSWORD must be provided via local .env.')

# 1. Superuser / Admin
user, created = User.objects.get_or_create(email='admin@localhost', defaults={'is_staff': True})
user.set_password(admin_password)
user.is_staff = True
user.save()

# 2. Organizer
org, _ = Organizer.objects.get_or_create(slug='sqe', defaults={'name': 'SE3002 Quality Engineering Org'})

# 3. Privileged Team with full permissions & API Token
admin_team, _ = Team.objects.get_or_create(
    organizer=org,
    name='Admin Team',
    defaults={
        'all_events': True,
        'all_event_permissions': True,
        'all_organizer_permissions': True
    }
)
admin_team.members.add(user)

token, _ = TeamAPIToken.objects.get_or_create(team=admin_team, name='SQE Test API Token')

# 4. Read-Only Team & Auditor User (Role 2)
auditor_user, _ = User.objects.get_or_create(email='auditor@localhost', defaults={'is_staff': False})
auditor_user.set_password(auditor_password)
auditor_user.is_staff = False
auditor_user.save()

read_team, _ = Team.objects.get_or_create(
    organizer=org,
    name='Auditor Read-Only Team',
    defaults={
        'all_events': True,
        'all_event_permissions': False,
        'all_organizer_permissions': False,
        'limit_event_permissions': {'can_view_orders': True, 'event.orders:read': True},
        'limit_organizer_permissions': {}
    }
)
read_team.members.add(auditor_user)
readonly_token, _ = TeamAPIToken.objects.get_or_create(team=read_team, name='Auditor Read Token')

# 5. Scoped Event, Item, and Quota Creation
with scope(organizer=org):
    event, _ = Event.objects.get_or_create(
        organizer=org,
        slug='sqe2026',
        defaults={
            'name': {'en': 'SQE International Conference 2026'},
            'currency': 'EUR',
            'date_from': now() + timedelta(days=30),
            'date_to': now() + timedelta(days=32),
            'live': True
        }
    )
    event.live = True
    event.plugins = 'pretix.plugins.banktransfer,pretix.plugins.manualpayment'
    event.settings.locales = ['en', 'de']
    event.settings.payment_banktransfer__enabled = True
    event.settings.payment_banktransfer_bank_details = 'IBAN DE89370400440532013000'
    event.settings.payment_manualpayment__enabled = True
    event.settings.payment_manual__enabled = True
    event.settings.waiting_list_enabled = True
    event.save()

    # 6. Item (Product)
    item, _ = Item.objects.get_or_create(
        event=event,
        default_price=Decimal('50.00'),
        defaults={
            'name': {'en': 'Conference Admission Ticket'},
            'active': True
        }
    )
    item.active = True
    item.save()

    # 7. Quota (Size: 10)
    quota, _ = Quota.objects.get_or_create(
        event=event,
        name='General Admission Quota',
        defaults={'size': 10}
    )
    quota.size = 10
    quota.items.set([item])
    quota.save()

    print(f"SEED_SUCCESS:TOKEN={token.token}:READONLY_TOKEN={readonly_token.token}:ORGANIZER={org.slug}:EVENT={event.slug}:ITEM_ID={item.id}:QUOTA_ID={quota.id}")
