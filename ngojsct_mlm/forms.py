from django import forms
from .models import *
from collections import OrderedDict

class MemberRegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = MemberModel
        fields = [
            'senior_ID', 'senior_Name',  'applicant_name','phone_number',
            'state', 'city', 'pincode','address','user_type' #'registration_fee'
        ]

    def __init__(self, *args, **kwargs):
        super(MemberRegistrationForm, self).__init__(*args, **kwargs)

        # Apply common form-control class
        for field in self.fields:
            if field not in ['password', 'password1']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

        # Dropdowns with dynamic options if needed
        self.fields['state'].widget = forms.Select(
            choices=[('', 'Select')] + [(data.name, data.name) for data in StateModel.objects.filter(status=1)],
            attrs={'class': 'form-control','onchange': "handleDropdownChange(this, 'id_city', '/cascade_ajax/', 'state')"}
        )
        self.fields['city'].widget = forms.Select(
            choices=[('', 'Select')] + [(data.name, data.name) for data in CityModel.objects.filter(status=1)],
            attrs={'class': 'form-control'}
        )
        self.fields['user_type'].widget = forms.Select(attrs={'class': 'form-control','placeholder': 'Enter your area',},choices=[ (' ', 'Select'),
        ('Individual', 'Individual'),
        ('Organisation', 'Organisation'),])
        self.fields['address'].widget = forms.Textarea(attrs={'class': 'form-control','rows':2})
        self.fields = OrderedDict([
    ('senior_ID', self.fields['senior_ID']),
    ('senior_Name', self.fields['senior_Name']),
    ('applicant_name', self.fields['applicant_name']),
    ('email', self.fields['email']),
    ('phone_number', self.fields['phone_number']),
    ('address', self.fields['address']),
    ('user_type', self.fields['user_type']),
    ('password', self.fields['password']),
    ('password1', self.fields['password1']),
    ('state', self.fields['state']),
    ('city', self.fields['city']),
    ('pincode', self.fields['pincode']),
    # ('registration_fee', self.fields['registration_fee']),
])

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password1 = cleaned_data.get("password1")

        if password and password1 and password != password1:
            self.add_error('password1', "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        member = super().save(commit=False)

        # Create linked user
        user = CustomUser.objects.create_user(
            email=self.cleaned_data['email'],
            applicant_name=self.cleaned_data.get('applicant_name') or self.cleaned_data['phone_number'],
            password=self.cleaned_data['password'],
            user_type='member'
        )

        # Auto-generate memberID if needed
        last_member = MemberModel.objects.order_by('-id').first()
        if last_member and last_member.id:
            new_member_id = f"JSCT{last_member.id + 1:06d}"
        else:
            new_member_id = "JSCT000001"
        user.memberID = new_member_id
        user.save()

        # Assign user to member
        member.user_detail = user

        if commit:
            member.save()

        return member


class MemberLoginForm(forms.Form):
    username = forms.CharField(label="Email or Member ID")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    def __init__(self, *args, **kwargs):
        super(MemberLoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email or Member ID'})
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})