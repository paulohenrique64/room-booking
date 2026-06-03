from .notifications import build_notification_summary


def notifications(request):
    return {
        'notification_summary': build_notification_summary(request.user),
    }
