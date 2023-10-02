from datetime import timedelta, datetime

from crm.models import Customer
from elk.celery import app as celery
from market.models import Class
from timeline.signals import class_starting_student, class_starting_teacher, week_without_classes


@celery.task
def notify_15min_to_class():
    for i in Class.objects.starting_soon(timedelta(minutes=30)).filter(pre_start_notifications_sent_to_teacher=False).distinct('timeline'):
        for other_class_with_the_same_timeline in Class.objects.starting_soon(timedelta(minutes=30)).filter(timeline=i.timeline):
            """
            Set all other starting classes as notified either.
            """
            other_class_with_the_same_timeline.pre_start_notifications_sent_to_teacher = True
            other_class_with_the_same_timeline.save()
        class_starting_teacher.send(sender=notify_15min_to_class, instance=i)

    for i in Class.objects.starting_soon(timedelta(minutes=30)).filter(pre_start_notifications_sent_to_student=False):
        i.pre_start_notifications_sent_to_student = True
        i.save()
        class_starting_student.send(sender=notify_15min_to_class, instance=i)


@celery.task
def notify_week_without_classes():
    last_week = datetime.now() - timedelta(weeks=1)

    target_users = Customer.objects.filter(
        classes__timeline_start__lte=last_week
    ).distinct().values_list('user', flat=True)

    for user in target_users:
        week_without_classes.send(sender=notify_week_without_classes, instance=user)

