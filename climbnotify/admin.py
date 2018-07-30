from django.contrib import admin
from .models import Mountains
from .models import User
from .models import ClimbingRecord
from .models import ActivatedUsers
from .models import MapPositionData

# Register your models here.
admin.site.register(Mountains)
admin.site.register(User)
admin.site.register(ClimbingRecord)
admin.site.register(ActivatedUsers)
admin.site.register(MapPositionData)