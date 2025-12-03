from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser, Student, Item, Registration


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )

    class Meta:
        model = CustomUser                         # ✔ FIXED
        fields = ['username', 'email', 'college_name', 'role']

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'college_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')

        if password != confirm:
            raise forms.ValidationError("Passwords do not match")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user



from django import forms
from .models import Student, Item, Registration


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "name",
            "id_card",
            "date_of_birth",
            "department",
            "year_of_joining",
            "current_year",
        ]


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name", "max_participants", "category"]


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["student", "item"]


from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Student
        fields = [
            "name", "id_card", "date_of_birth",
            "department", "year_of_joining", "current_year"
        ]


class TeamCreateForm(forms.Form):
    item = forms.ChoiceField()
    students = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)
