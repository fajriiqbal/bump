from django.contrib import admin
from .models import Bill, CashAccount, Expense, Income, Payment, PaymentType, WhatsAppReminderSchedule


admin.site.register(PaymentType)
admin.site.register(Bill)
admin.site.register(Payment)
admin.site.register(CashAccount)
admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(WhatsAppReminderSchedule)
