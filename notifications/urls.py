from django.urls import path
from .views import (
    MessageTemplateCreateView,
    MessageTemplateDeleteView,
    MessageTemplateListView,
    MessageTemplateUpdateView,
    NotificationIndexView,
    SendBillReminderView,
    SendStudentReminderView,
    WhatsAppGatewayCreateView,
    WhatsAppGatewayDeleteView,
    WhatsAppGatewayListView,
    WhatsAppGatewayUpdateView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationIndexView.as_view(), name="index"),
    path("gateway/", WhatsAppGatewayListView.as_view(), name="gateway_list"),
    path("gateway/tambah/", WhatsAppGatewayCreateView.as_view(), name="gateway_create"),
    path("gateway/<int:pk>/edit/", WhatsAppGatewayUpdateView.as_view(), name="gateway_update"),
    path("gateway/<int:pk>/hapus/", WhatsAppGatewayDeleteView.as_view(), name="gateway_delete"),
    path("templates/", MessageTemplateListView.as_view(), name="template_list"),
    path("templates/tambah/", MessageTemplateCreateView.as_view(), name="template_create"),
    path("templates/<int:pk>/edit/", MessageTemplateUpdateView.as_view(), name="template_update"),
    path("templates/<int:pk>/hapus/", MessageTemplateDeleteView.as_view(), name="template_delete"),
    path("bills/<int:bill_id>/send/", SendBillReminderView.as_view(), name="send_bill_reminder"),
    path("students/<int:student_id>/send/", SendStudentReminderView.as_view(), name="send_student_reminder"),
]
