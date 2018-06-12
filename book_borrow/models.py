from django.db import models


class Book(models.Model):
    book_name = models.CharField(verbose_name='图书名称', max_length=255, blank=False, null=False, unique=True)
    author = models.CharField(verbose_name='作者', max_length=100, blank=False, null=False)
    brief_introduction = models.CharField(verbose_name='简介', max_length=4096, default='', null=False)
    price = models.DecimalField(verbose_name='价格', max_digits=8, decimal_places=2)
    book_num = models.IntegerField(verbose_name='图书数量', default=1, null=False)
    referee = models.CharField(verbose_name='推荐人', max_length=100, default='', null=False)
    recommended_reasons = models.CharField(verbose_name='推荐理由', max_length=4096, default='', null=False)
    press = models.CharField(verbose_name='出版社', max_length=1024, default='', null=False)
    borrow_num = models.IntegerField(verbose_name='借阅数量', default=0, null=False)
    cover_img_pathname = models.CharField(verbose_name='封面图片路径名',
                                          max_length=255, default='', null=False)


class BookClass(models.Model):
    parent_id = models.IntegerField(verbose_name='父Id', blank=False, null=False)
    name = models.CharField(verbose_name='类型名称', max_length=255, blank=False, null=False)
    book_list = models.ManyToManyField(Book)


class BookBorrowItem(models.Model):
    book_name = models.CharField(verbose_name='图书名称', max_length=255, blank=False, null=False)
    borrower = models.CharField(verbose_name='借阅人', max_length=100, blank=False, null=False)
    borrower_department = models.CharField(verbose_name='借阅人所属部门', max_length=100, blank=False, null=False)
    borrowed_time = models.DateTimeField(verbose_name='借阅时间', blank=False, null=False)
    end_time = models.DateTimeField(verbose_name='截止时间', blank=False, null=False)


class BookBorrowHistory(models.Model):
    book_name = models.CharField(verbose_name='图书名称', max_length=255, blank=False, null=False)
    borrower = models.CharField(verbose_name='借阅人', max_length=100, blank=False, null=False)
    borrower_department = models.CharField(verbose_name='借阅人所属部门', max_length=100, blank=False, null=False)
    borrowed_time = models.DateTimeField(verbose_name='借阅时间', blank=False, null=False)
    book_return_time = models.DateTimeField(verbose_name='还书时间', blank=False, null=False)
