from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import PondokProfile


class StyledFormMixin:
    def _style_fields(self):
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            base = "input-modern"
            if getattr(field.widget, "input_type", "") in {"checkbox", "radio"}:
                field.widget.attrs["class"] = "h-4 w-4 rounded border-stone-300 text-brown-primary focus:ring-gold-soft"
            elif getattr(field.widget, "input_type", "") == "file":
                field.widget.attrs["class"] = (
                    "block w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 "
                    "text-sm text-brown-dark file:mr-4 file:rounded-xl file:border-0 "
                    "file:bg-cream file:px-4 file:py-2 file:text-brown-dark"
                )
            elif "class" in field.widget.attrs:
                field.widget.attrs["class"] = f"{classes} {base}".strip()
            else:
                field.widget.attrs["class"] = base


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "input-modern"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input-modern"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Username"})
        self.fields["password"].widget.attrs.update({"placeholder": "Kata sandi"})


class PondokProfileForm(forms.ModelForm):
    class Meta:
        model = PondokProfile
        fields = [
            "nama_pondok",
            "alamat",
            "kota",
            "telepon",
            "email",
            "kepala_pesantren",
            "bendahara_nama",
            "bendahara_telepon",
            "wa_admin",
            "bank_nama",
            "bank_nomor_rekening",
            "bank_atas_nama",
            "qris_url",
            "website",
            "motto",
            "catatan",
        ]
        widgets = {
            "catatan": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = {"nama_pondok", "alamat", "kota", "telepon", "kepala_pesantren"}
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.Textarea,)):
                widget.attrs["class"] = "input-modern min-h-[120px]"
            else:
                widget.attrs["class"] = "input-modern"
            if name in required_fields:
                field.required = True
            else:
                field.required = False
        self.fields["motto"].help_text = "Opsional, dipakai sebagai tagline di tampilan dan export."
        self.fields["qris_url"].help_text = "Opsional, tempelkan link QRIS untuk pembayaran cepat."
        self.fields["wa_admin"].help_text = "Nomor WhatsApp admin untuk konfirmasi pembayaran dan pertanyaan wali santri."
