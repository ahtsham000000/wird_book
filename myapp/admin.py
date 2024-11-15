from django.contrib import admin
from .models import PhoneNumber,CommunityMember,Token ,Khitmah ,Juz

admin.site.register(Khitmah)
admin.site.register(Token)
admin.site.register(PhoneNumber)
admin.site.register(CommunityMember)
admin.site.register(Juz)