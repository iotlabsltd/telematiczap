from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group
from .models import User, Message, DataAfter, DataBefore, DataFormat, DataFormatClues

admin.site.register(User, UserAdmin)
admin.site.register(DataBefore)
admin.site.register(DataFormat)
admin.site.register(DataFormatClues)
admin.site.register(DataAfter)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'message')
    list_filter = ('email',)
    search_fields = ('email', 'message')
    

admin.autodiscover()

