from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import AssetAssignment, AuditLog, Notification


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_overdue_assignments(self):
    """Find overdue assignments, create notifications and attempt email sends with retries."""
    overdue = AssetAssignment.objects.filter(
        date_due__lt=timezone.now(),
        date_returned__isnull=True
    ).select_related('asset', 'assigned_to', 'assigned_by')

    notifications_created = 0
    email_notifications = 0

    for assignment in overdue:
        try:
            subject = f'Overdue Asset Alert: {assignment.asset.asset_tag}'
            message = (
                f'Asset {assignment.asset.name} ({assignment.asset.asset_tag}) is overdue.\n'
                f'Assigned to: {assignment.assigned_to.get_full_name() or assignment.assigned_to.username}\n'
                f'Due date: {assignment.date_due}\n'
                f'Please follow up.'
            )

            recipients = []
            if assignment.assigned_by:
                Notification.objects.create(
                    user=assignment.assigned_by,
                    message=message,
                    link=f'/assignments/{assignment.id}/',
                    level='ALERT'
                )
                notifications_created += 1
                if assignment.assigned_by.email:
                    recipients.append(assignment.assigned_by.email)

            if assignment.assigned_to:
                Notification.objects.create(
                    user=assignment.assigned_to,
                    message=message,
                    link=f'/assignments/{assignment.id}/',
                    level='WARNING'
                )
                notifications_created += 1
                if assignment.assigned_to.email:
                    recipients.append(assignment.assigned_to.email)

            # Attempt email send if configured
            if recipients and getattr(settings, 'EMAIL_HOST', ''):
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
                    email_notifications += 1
                except Exception as exc:
                    try:
                        raise self.retry(exc=exc)
                    except MaxRetriesExceededError:
                        AuditLog.objects.create(
                            user=None,
                            action='EXPORT',
                            model_name='AssetAssignment',
                            object_id=str(assignment.id),
                            description=f'Failed to send overdue email after retries: {str(exc)}'
                        )

            # Record audit log of notification creation
            AuditLog.objects.create(
                user=None,
                action='EXPORT',
                model_name='AssetAssignment',
                object_id=str(assignment.id),
                description=f'Created {notifications_created} notifications for overdue assignment {assignment.id}'
            )

        except Exception as e:
            AuditLog.objects.create(
                user=None,
                action='EXPORT',
                model_name='AssetAssignment',
                object_id=str(assignment.id),
                description=f'Unexpected error in overdue task: {str(e)}'
            )

    return {'overdue_count': overdue.count(), 'notifications_created': notifications_created, 'email_notifications': email_notifications}
