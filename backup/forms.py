from django import forms


class BackupRestoreForm(forms.Form):
    backup_file = forms.FileField(
        label="File Backup (.json)",
        help_text="Pilih file .json hasil backup untuk dipulihkan.",
    )
    confirm_restore = forms.BooleanField(
        label="Saya memahami restore akan mengganti data sesuai file backup",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["backup_file"].widget.attrs.update(
            {
                "accept": ".json",
                "class": "block w-full appearance-none border-0 bg-transparent px-0 py-3 text-sm text-brown-dark file:mr-4 file:rounded-xl file:border-0 file:bg-cream file:px-4 file:py-2 file:text-brown-dark",
            }
        )
        self.fields["confirm_restore"].widget.attrs.update(
            {
                "class": "h-4 w-4 rounded border-stone-300 text-brown-primary focus:ring-gold-soft",
            }
        )

    def clean_backup_file(self):
        uploaded = self.cleaned_data["backup_file"]
        if not uploaded.name.lower().endswith(".json"):
            raise forms.ValidationError("File backup harus berformat .json.")
        return uploaded
