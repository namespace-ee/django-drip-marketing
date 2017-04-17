# -*- coding: utf-8
import dateparser
import functools
import logging
import operator
import uuid
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.template import Context, Template
from django.utils import timezone


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Drip(BaseModel):
    name = models.CharField(max_length=255, unique=True, verbose_name='Drip Name',
                            help_text='A unique name for this drip.')
    from_email = models.EmailField(null=True, blank=True,
                                   help_text='Set a custom from email.')
    sender_name = models.CharField(max_length=150, null=True, blank=True,
                                   help_text='Set a name for a custom from email.')
    subject_template = models.CharField(max_length=200, null=True, blank=True)
    text_template = models.TextField(null=True, blank=True)
    html_template = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def subject(self, user):
        return Template(self.subject_template).render(Context({
            'user': user
        }))

    def text(self, user):
        return Template(self.text_template).render(Context({
            'user': user
        }))

    def html(self, user):
        html_body = Template(self.html_template).render(Context({
            'user': user
        }))
        if getattr(settings, 'DRIP_PREMAILER', False):
            from premailer import transform
            html_body = transform(html_body)
        return html_body

    def run(self, now=timezone.now()):
        if not self.from_email:
            self.from_email = getattr(settings, 'DRIP_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)

        queryset = self.apply_rules(now=now)
        for user in queryset:
            SentDrip.objects.get_or_create(
                drip=self,
                user=user,
                defaults={
                    'from_email': self.from_email,
                    'sender_name': self.sender_name if self.sender_name else '',
                    'subject': self.subject(user),
                    'text_body': self.text(user),
                    'html_body': self.html(user)
                }
            )

    def apply_rules(self, now=timezone.now()):
        qs = get_user_model().objects.all()

        # Exclude sent drips
        sent_drips_user_ids = SentDrip.objects.filter(drip=self).\
            values_list('user', flat=True)
        qs = qs.exclude(id__in=sent_drips_user_ids)

        clauses = {
            'filter': [],
            'exclude': []
        }

        for rule in self.drip_rules.all():
            clause = clauses.get(rule.method_type, clauses['filter'])

            kwargs = rule.filter_kwargs(qs, now=now)
            clause.append(Q(**kwargs))

            qs = rule.apply_any_annotation(qs)

        if clauses['exclude']:
            qs = qs.exclude(functools.reduce(operator.or_, clauses['exclude']))
        qs = qs.filter(*clauses['filter'])

        return qs


class DripRule(BaseModel):
    METHOD_TYPES = (
        ('filter', 'Filter'),
        ('exclude', 'Exclude'),
    )

    LOOKUP_TYPES = (
        ('exact', 'exactly'),
        ('iexact', 'exactly (case insensitive)'),
        ('contains', 'contains'),
        ('icontains', 'contains (case insensitive)'),
        ('regex', 'regex'),
        ('iregex', 'contains (case insensitive)'),
        ('gt', 'greater than'),
        ('gte', 'greater than or equal to'),
        ('lt', 'less than'),
        ('lte', 'less than or equal to'),
        ('startswith', 'starts with'),
        ('endswith', 'starts with'),
        ('istartswith', 'ends with (case insensitive)'),
        ('iendswith', 'ends with (case insensitive)'),
    )
    drip = models.ForeignKey(Drip, related_name='drip_rules')
    method_type = models.CharField(max_length=12, default='filter', choices=METHOD_TYPES)
    field_name = models.CharField(max_length=128, verbose_name='Field name of User')
    lookup_type = models.CharField(max_length=12, default='exact', choices=LOOKUP_TYPES)
    field_value = models.CharField(
        max_length=255,
        help_text=(
            'Can be anything from a number, to a string. Or, do `now-7 days`'
            'or `today+3 days` for fancy timedelta.'
        )
    )

    def clean(self):
        try:
            self.apply(get_user_model().objects.all())
        except Exception as e:
            raise ValidationError(
                '%s raised trying to apply rule: %s' % (type(e).__name__, e))

    @property
    def annotated_field_name(self):
        field_name = self.field_name
        if field_name.endswith('__count'):
            agg, _, _ = field_name.rpartition('__')
            field_name = 'num_%s' % agg.replace('__', '_')

        return field_name

    def apply_any_annotation(self, qs):
        if self.field_name.endswith('__count'):
            field_name = self.annotated_field_name
            agg, _, _ = self.field_name.rpartition('__')
            qs = qs.annotate(**{field_name: models.Count(agg, distinct=True)})
        return qs

    def filter_kwargs(self, qs, now=timezone.now):
        # Support Count() as m2m__count
        field_name = self.annotated_field_name
        field_name = '__'.join([field_name, self.lookup_type])
        field_value = self.field_value

        # Timezone
        timezone = getattr(settings, 'TIME_ZONE', 'UTC')

        # set time deltas and dates
        if self.field_value.startswith('now-'):
            field_value = self.field_value.replace('now-', '')
            field_value = dateparser.parse(field_value, settings={
                'TIMEZONE': timezone,
                'RETURN_AS_TIMEZONE_AWARE': True
            })
        elif self.field_value.startswith('now+'):
            field_value = self.field_value.replace('now+', '')
            field_value = dateparser.parse(field_value, settings={
                'TIMEZONE': timezone,
                'RETURN_AS_TIMEZONE_AWARE': True
            })
        elif self.field_value.startswith('today-'):
            field_value = self.field_value.replace('today-', '')
            field_value = dateparser.parse(field_value, settings={
                'TIMEZONE': timezone,
                'RETURN_AS_TIMEZONE_AWARE': True
            }).date()
        elif self.field_value.startswith('today+'):
            field_value = self.field_value.replace('today+', '')
            field_value = dateparser.parse(field_value, settings={
                'TIMEZONE': timezone,
                'RETURN_AS_TIMEZONE_AWARE': True
            }).date()

        # F expressions
        if self.field_value.startswith('F_'):
            field_value = self.field_value.replace('F_', '')
            field_value = models.F(field_value)

        # set booleans
        if self.field_value == 'True':
            field_value = True
        if self.field_value == 'False':
            field_value = False

        kwargs = {
            field_name: field_value
        }
        return kwargs

    def apply(self, qs, now=timezone.now):

        kwargs = self.filter_kwargs(qs, now)
        qs = self.apply_any_annotation(qs)

        if self.method_type == 'filter':
            return qs.filter(**kwargs)
        elif self.method_type == 'exclude':
            return qs.exclude(**kwargs)

        # catch as default
        return qs.filter(**kwargs)


class SentDrip(BaseModel):
    STATE_QUEUED = 'queued'
    STATE_SENT = 'sent'
    STATES = (
        (STATE_QUEUED, 'Queued'),
        (STATE_SENT, 'Sent'),
    )
    drip = models.ForeignKey('drip_marketing.Drip', related_name='sent_drips')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_drips')
    from_email = models.EmailField()
    sender_name = models.CharField(max_length=100)
    subject = models.TextField()
    text_body = models.TextField()
    html_body = models.TextField()
    state = models.CharField(max_length=20, choices=STATES, default='queued')

    def __str__(self):
        return '{} - {}'.format(self.drip.name, self.user.email)

    def send(self):
        message = EmailMultiAlternatives(
            subject=self.subject,
            from_email=self.from_email,
            to=[self.user.email],
            body=self.text_body
        )
        if html_body:
            message.attach_alternative(self.html_body, 'text/html')

        result = message.send(fail_silently=False)
        if result:
            self.state = self.STATE_SENT
            self.save()
        return result
