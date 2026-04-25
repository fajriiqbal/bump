from django import forms
from .models import Student


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            input_type = getattr(widget, "input_type", "")
            if input_type in {"checkbox", "radio"}:
                widget.attrs["class"] = "h-4 w-4 rounded border-stone-300 text-brown-primary focus:ring-gold-soft"
            elif input_type == "file":
                widget.attrs["class"] = "block w-full appearance-none border-0 bg-transparent px-0 py-3 text-sm text-brown-dark file:mr-4 file:rounded-xl file:border-0 file:bg-cream file:px-4 file:py-2 file:text-brown-dark"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = "input-modern pr-8"
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = "input-modern min-h-[140px]"
            else:
                current = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{current} input-modern".strip()
            if input_type == "text" and name in {"nis", "nama_lengkap", "kelas", "kamar", "nama_ayah", "nama_ibu", "nama_wali", "no_wa_wali", "tahun_ajaran"}:
                widget.attrs.setdefault("placeholder", field.label)


class StudentForm(StyledModelForm):
    class Meta:
        model = Student
        fields = "__all__"
        widgets = {
            "tanggal_lahir": forms.DateInput(attrs={"type": "date"}),
            "tanggal_masuk": forms.DateInput(attrs={"type": "date"}),
        }


class StudentImportForm(forms.Form):
    file = forms.FileField(
        label="File Import",
        help_text="Upload file CSV atau XLSX dengan kolom yang sesuai template.",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx"}),
    )
    update_existing = forms.BooleanField(
        label="Perbarui data yang sudah ada",
        required=False,
        initial=True,
        help_text="Jika aktif, NIS yang sudah ada akan di-update. Jika tidak, data lama tetap dipertahankan.",
    )
