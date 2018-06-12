from django import forms
from django.contrib.auth.models import User


class ChangePasswordForm(forms.Form):
    username = forms.CharField(required=True, error_messages={'required': '用户名不能为空'})
    password = forms.CharField(required=True, error_messages={'required': '密码不能为空'})
    sure_password = forms.CharField(required=True, error_messages={'required': '确认密码不能为空'})

    def clean_username(self):
        username = self.cleaned_data['username']

        save_user_count = User.objects.filter(username=username).count()
        if save_user_count != 1:
            raise forms.ValidationError('用户名异常，请联系管理员核查')

        return username

    def clean_sure_password(self):
        password = self.cleaned_data['password']
        sure_password = self.cleaned_data['sure_password']

        if password == 'sxfs123456':
            raise forms.ValidationError('密码不可与默认密码一致')

        if not password or not sure_password or password != sure_password:
            raise forms.ValidationError('密码填写不匹配')

        return password
