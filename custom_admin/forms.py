from myapp.models import CommunityMember,PhoneNumber
from django import forms

class AdminLoginForm (forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )



class EditPhoneNumberForm(forms.ModelForm):
    class Meta:
        model = PhoneNumber
        fields = ['number', 'is_verified', 'role']
        
        
        
class AssignAdminForm(forms.ModelForm):
    class Meta:
        model = CommunityMember
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'})
        }
        
        
        
class EditMemberStatusForm(forms.ModelForm):
    class Meta:
        model = CommunityMember
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
