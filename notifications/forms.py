from django import forms

from .models import MessageTemplate, WhatsAppGatewayConfig


class StyledNotificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            input_type = getattr(widget, "input_type", "")
            if input_type in {"checkbox", "radio"}:
                widget.attrs["class"] = "h-4 w-4 rounded border-stone-300 text-brown-primary focus:ring-gold-soft"
            elif input_type == "file":
                widget.attrs["class"] = "block w-full appearance-none border-0 bg-transparent px-0 py-3 text-sm text-brown-dark file:mr-4 file:rounded-xl file:border-0 file:bg-cream file:px-4 file:py-2 file:text-brown-dark"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = "input-modern pr-8"
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = "input-modern min-h-[160px]"
            else:
                current = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{current} input-modern".strip()


class WhatsAppGatewayForm(StyledNotificationForm):
    class Meta:
        model = WhatsAppGatewayConfig
        fields = "__all__"


class MessageTemplateForm(StyledNotificationForm):
    class Meta:
        model = MessageTemplate
        fields = "__all__"
