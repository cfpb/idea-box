from django.contrib.comments.signals import comment_was_posted
from django.dispatch import receiver
from idea.models import Idea


@receiver(comment_was_posted)
def send_idea_notifications(sender, comment, request, **kwargs):
    # If installed in collab
    try:
        from core.notifications.models import Notification
        from core.notifications.email import EmailInfo
        from core.helpers import normalize

        idea = comment.content_object

        title = u"%s %s commented on %s" % (normalize(comment.user.first_name),
                                            normalize(comment.user.last_name),
                                            idea.title)

        for user in idea.members:
            if user != comment.user:
                email_info = EmailInfo(
                                subject = title,
                                text_template = 'idea/email/new_comment.txt',
                                html_template = 'idea/email/new_comment.html',
                                to_address = user.email,
                            )
                Notification.set_notification(comment.user, comment.user, "commented", idea,
                                              user, title, idea.url(), email_info)
    except ImportError:
        pass