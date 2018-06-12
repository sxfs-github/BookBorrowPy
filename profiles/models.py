from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')
    center = models.CharField(verbose_name='所属中心', max_length=255, blank=False, null=False)
    department = models.CharField(verbose_name='部门', max_length=255, blank=False, null=False)
    position = models.CharField(verbose_name='岗位', max_length=255, blank=False, null=False)

    def __str__(self):
        return self.user.first_name

    class Meta:
        verbose_name = "用户配置"
        verbose_name_plural = "用户配置"
        permissions = (
            ('write_book_info', '录入图书信息'),
            ('borrow_book', '借书'),
            ('return_book', '还书'),
            ('see_book_borrow_history', '查看历史借阅记录'),
            ('edit_user', '编辑用户'),
        )

