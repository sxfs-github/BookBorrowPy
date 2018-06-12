from django import forms


class InputBookForms(forms.Form):
    book_name = forms.CharField(required=True, error_messages={'required': '必须输入书名'})
    author = forms.CharField(required=True, error_messages={'required': '必须输入作者'})
    price = forms.DecimalField(required=True, decimal_places=2,
                               error_messages={'required': '必须输入定价',
                                               'decimal_places': '价格格式不正确'})
    book_num = forms.IntegerField(required=True, min_value=1,
                                  error_messages={'required': '必须输入图书数量',
                                                  'min_value': '请输入正确的图书数量'})
