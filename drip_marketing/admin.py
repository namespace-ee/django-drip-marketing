import itertools
import operator
from datetime import timedelta

from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from drip_marketing.models import Drip, DripRule, SentDrip


class DripRuleInline(admin.TabularInline):
    model = DripRule
    extra = 1


@admin.register(Drip)
class DripAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'from_email',
        'sender_name',
        'subject_template',
        'text_template',
        'active',
    ]
    inlines = [
        DripRuleInline,
    ]
    actions = [
        'run_drips'
    ]

    class Media:
        css = {
            'all': (
                '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/codemirror.min.css',
                '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/theme/monokai.min.css',
                'drip_marketing/css/admin.css',
            )
        }
        js = (
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/codemirror.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/addon/mode/overlay.min.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/addon/display/panel.min.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/mode/xml/xml.min.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/mode/css/css.min.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/mode/htmlmixed/htmlmixed.min.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/mode/javascript/javascript.min.js',
            '//cdnjs.cloudflare.com/ajax/libs/codemirror/5.25.0/mode/django/django.min.js',
            'drip_marketing/js/admin.js',
        )

    def build_extra_context(self, extra_context):
        extra_context = extra_context or {}
        # TODO: Add context required
        return extra_context

    def add_view(self, request, extra_context=None):
        return super(DripAdmin, self).add_view(
            request, extra_context=self.build_extra_context(extra_context)
        )

    def change_view(self, request, object_id, extra_context=None):
        return super(DripAdmin, self).change_view(
            request, object_id, extra_context=self.build_extra_context(extra_context)
        )

    def run_drips(self, request, queryset):
        for drip in queryset:
            drip.run()
    run_drips.short_description = 'Run drips'

    def get_urls(self):
        urls = super(DripAdmin, self).get_urls()
        return [
            url(r'^admin/drip_marketing/timeline/(?P<drip_id>[0-9A-Za-z\-]+)/$',
                self.view_drip_timeline, name='drip_timeline'),
            url(r'^admin/drip_marketing/email/(?P<drip_id>[0-9A-Za-z\-]+)/(?P<user_id>[0-9A-Za-z\-]+)/$',
                self.view_drip_email, name='drip_email'),
        ] + urls

    def view_drip_email(self, request, drip_id, user_id):
        drip = get_object_or_404(Drip, id=drip_id)
        user = get_object_or_404(get_user_model(), id=user_id)

        return render(request, 'admin/drip_marketing/view.html', {
            'drip': drip,
            'user': user
        })

    def view_drip_timeline(self, request, drip_id, start_date=None, end_date=None):
        drip = get_object_or_404(Drip, id=drip_id)

        if not start_date:
            start_date = (timezone.now() - timedelta(days=7)).date()
        if not end_date:
            end_date = (timezone.now() + timedelta(days=7)).date()

        drips = []
        for i in range((end_date - start_date).days + 1):
            drip_date = (start_date + timedelta(days=i))
            queryset = drip.apply_rules(now=drip_date)

            for user in queryset:
                if not any(d['user'] == user for d in drips):
                    drips.append({
                        'id': drip.id,
                        'date': drip_date,
                        'user': user
                    })

        drips  = sorted(drips, key=operator.itemgetter('date'))
        grouped_drips = {}
        for key, group in itertools.groupby(drips, key=lambda x:x['date']):
            grouped_drips[key] = list(group)

        return render(request, 'admin/drip_marketing/timeline.html', {
            'drip': drip,
            'grouped_drips': grouped_drips
        })

@admin.register(SentDrip)
class SentDripAdmin(admin.ModelAdmin):
    list_display = [
        'state',
        'drip',
        'user',
        'subject',
        'from_email',
        'sender_name',
        'text_body',
        'created_at',
    ]
    readonly_fields = [
        'subject',
        'text_body',
        'html_body'
    ]
    ordering = ['-created_at']
    list_filter = [
        'state',
        'created_at'
    ]
    actions = [
        'send_queued_drips'
    ]

    def send_queued_drips(self, request, queryset):
        for drip in queryset.filter(state=SentDrip.STATE_QUEUED):
            drip.send()
    send_queued_drips.short_description = 'Send queued drips'
