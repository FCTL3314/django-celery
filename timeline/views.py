from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render
from django.views.generic.edit import CreateView, UpdateView

from elk.utils import date
from timeline.forms import EntryForm as TimelineEntryForm
from timeline.models import Entry as TimelineEntry


@staff_member_required
def calendar(request, username):
    return render(request, 'calendar/user.html', context={
        'object': get_object_or_404(User, username=username)
    })


class UserCtxMixin():
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = get_object_or_404(User, username=self.kwargs['username'])
        return context


class calendar_create(CreateView, UserCtxMixin):
    template_name = 'forms/entry_create.html'
    form_class = TimelineEntryForm

    def get_success_url(self):
        return reverse('timeline:timeline', kwargs=self.kwargs)


class calendar_update(UpdateView, UserCtxMixin):
    template_name = 'forms/entry_update.html'
    form_class = TimelineEntryForm
    model = TimelineEntry

    def get_success_url(self):
        return reverse('timeline:timeline',
                       kwargs={'username': self.kwargs['username']},
                       )


def calendar_delete(request, username, pk):
    user = get_object_or_404(User, username=username)
    entry = get_object_or_404(TimelineEntry, teacher=user, pk=pk)
    entry.active = 0
    entry.save()
    return redirect(reverse('timeline:timeline', kwargs={'username': username}))


@staff_member_required
def calendar_json(request, username):
    user = get_object_or_404(User, username=username)
    entries = []
    start = request.GET.get('start', date.ago(days=16))
    end = request.GET.get('end', date.fwd(days=16))

    for entry in get_list_or_404(TimelineEntry,
                                 start__range=(start, end),
                                 teacher=user
                                 ):
        entries.append(entry.as_dict())

    return JsonResponse(entries, safe=False)
