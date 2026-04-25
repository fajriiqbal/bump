from django.contrib import admin
from .models import MessageLog, MessageTemplate, WhatsAppGatewayConfig

admin.site.register(WhatsAppGatewayConfig)
admin.site.register(MessageTemplate)
admin.site.register(MessageLog)
