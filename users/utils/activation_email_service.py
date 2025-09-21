from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site

def send_activation_email(request, user, activation_link):
    """
    Sends activation email in plain text only.
    """
    current_site = get_current_site(request)
    site_name = current_site.name

    subject = render_to_string("users/emails/activation_subject.txt", {
        "site_name": site_name,
    }).strip()

    message = render_to_string("users/emails/activation_email.txt", {
        "user": user,
        "activation_link": activation_link,
        "site_name": site_name,
    })

    send_mail(subject, message, None, [user["email"]])
