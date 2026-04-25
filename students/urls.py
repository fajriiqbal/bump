from django.urls import path
from .views import (
    StudentCreateView,
    StudentDeleteView,
    StudentDetailView,
    StudentListView,
    StudentUpdateView,
    export_students_xlsx,
    import_students,
    import_students_csv,
)

app_name = "students"

urlpatterns = [
    path("", StudentListView.as_view(), name="list"),
    path("tambah/", StudentCreateView.as_view(), name="create"),
    path("<int:pk>/", StudentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", StudentUpdateView.as_view(), name="update"),
    path("<int:pk>/hapus/", StudentDeleteView.as_view(), name="delete"),
    path("export/xlsx/", export_students_xlsx, name="export_xlsx"),
    path("import/", import_students, name="import"),
    path("import/csv/", import_students_csv, name="import_csv"),
]
