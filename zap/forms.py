from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Field
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import User, DataBefore, DataFormat, DataAfter

# form for user profile update
class HomeForm(forms.Form):
    data_before = forms.FileField()
    data_format = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = '/'
        self.helper.add_input(Submit('submit', 'Submit'))


# forms for user registration
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Insert a valid e-mail address.', required=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# form for use login
class UserLoginForm(AuthenticationForm):
    pass
    #class Meta:
    #    model = User
    #    fields = ('username', 'password')


# form for user profile update
class UserEditForm(UserChangeForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    username = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'password', 'email')


class ContactForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = '/contact'
        self.helper.add_input(Submit('submit', 'Submit'))

    email = forms.EmailField(max_length=254)
    message = forms.CharField(max_length=254, widget=forms.Textarea)

