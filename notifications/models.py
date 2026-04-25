from django.db import models


class WhatsAppGatewayConfig(models.Model):
    name = models.CharField(max_length=100, default="Fonnte")
    api_url = models.URLField()
    api_key = models.CharField(max_length=255)
    sender = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)


class MessageTemplate(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    body = models.TextField()
    active = models.BooleanField(default=True)


class MessageLog(models.Model):
    status_choices = [("sent", "Sent"), ("failed", "Failed")]
    to_number = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=status_choices)
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
