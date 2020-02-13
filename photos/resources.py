from import_export import resources
from .models import UserGroup

class UserGroupResource(resources.ModelResource):
    class Meta:
        model = UserGroup