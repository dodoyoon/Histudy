from django.contrib import admin

# Register your models here.

from .models import Data, Verification, UserInfo
from import_export.admin import ImportExportModelAdmin

admin.site.register(Data)
admin.site.register(Verification)
admin.site.register(UserInfo)
