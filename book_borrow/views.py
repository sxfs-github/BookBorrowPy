
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, FileResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.conf import settings

from profiles.models import UserProfile

from BookBorrowPy import error_code
from .forms import InputBookForms
from .models import BookClass, Book, BookBorrowItem, BookBorrowHistory
import json
import time
import os
import datetime
import pymysql
import pandas as pd


# 图书管理系统首页
@require_GET
def index(request):
    search_name = request.GET.get('search_name')
    main_class_id = request.GET.get('main_class_id')
    child_class_id = request.GET.get('child_class_id')
    if search_name is None:
        search_name = ''
    if main_class_id is None:
        main_class_id = '-1'
    if child_class_id is None:
        child_class_id = '-1'

    if search_name == '':
        if child_class_id == '-1':
            if main_class_id == '-1':
                book_list = Book.objects.values('id', 'book_name', 'brief_introduction', 'cover_img_pathname')
            else:
                search_book_class = BookClass.objects.get(id=main_class_id)
                book_list = search_book_class.book_list.all()
        else:
            search_book_class = BookClass.objects.get(id=child_class_id)
            book_list = search_book_class.book_list.all()
    else:
        book_list_search = Book.objects.values('id', 'book_name', 'brief_introduction', 'cover_img_pathname'). \
            filter(book_name__contains=search_name)
        if child_class_id == '-1':
            if main_class_id == '-1':
                book_list = book_list_search
            else:
                search_book_class = BookClass.objects.get(id=main_class_id)
                book_list = search_book_class.book_list.all() | book_list_search
        else:
            search_book_class = BookClass.objects.get(id=child_class_id)
            book_list = search_book_class.book_list.all() | book_list_search

    paginator = Paginator(book_list, 4)

    page = request.GET.get('page')

    book_main_class_list = BookClass.objects.filter(parent_id=0)
    if len(book_main_class_list) == 0:
        book_main_class_list = []
        book_child_class_list = []
    else:
        if main_class_id != '':
            book_child_class_list = BookClass.objects.filter(parent_id=main_class_id)
        else:
            book_child_class_list = BookClass.objects.filter(parent_id=book_main_class_list[0].id)
            if len(book_child_class_list) == 0:
                book_child_class_list = []
    try:
        books = paginator.page(page)
    except PageNotAnInteger:
        books = paginator.page(1)
    except EmptyPage:
        books = paginator.page(paginator.num_pages)
    return render(request, 'index.html', {
        'books': books,
        'book_main_class_list': book_main_class_list,
        'book_child_class_list': book_child_class_list,
        'search_name': search_name,
        'main_class_id': int(main_class_id),
        'child_class_id': int(child_class_id)
    })


# 图书列表
@require_GET
def book_lists(request):
    book_list = Book.objects.values('id', 'book_name', 'author',  'book_num', 'borrow_num')

    paginator = Paginator(book_list, 10)

    page = request.GET.get('page')

    try:
        books = paginator.page(page)
    except PageNotAnInteger:
        books = paginator.page(1)
    except EmptyPage:
        books = paginator.page(paginator.num_pages)
    return render(request, 'book_list.html', {
        'books': books
    })


# 跳转登记图书信息
@login_required(login_url='login:login')
@require_GET
def input_book_info(request):
    book_main_class_list = BookClass.objects.filter(parent_id=0)
    if len(book_main_class_list) == 0:
        return render(request, 'input_book_info.html', {
            'book_main_class_list': [],
            'book_child_class_list': []
        })

    book_child_class_list = BookClass.objects.filter(parent_id=book_main_class_list[0].id)
    return render(request, 'input_book_info.html', {
        'book_main_class_list': list(book_main_class_list),
        'book_child_class_list': list(book_child_class_list)
    })


# 图书类型child
@require_GET
def update_child_class(request, main_class_id):
    book_child_class_list = BookClass.objects.values('id', 'name').filter(parent_id=main_class_id)
    return HttpResponse(json.dumps({
        'book_child_class_list': list(book_child_class_list)
    }))


# 登记图书信息
@login_required(login_url='login:login')
@require_POST
def commit_book_info(request):
    form = InputBookForms(request.POST)
    if not form.is_valid():
        data = {'code': error_code.INSERT_ERROR, 'msg': '登记图书失败'}
        return HttpResponse(json.dumps(data))
    if request.POST.get('id') == '':
        now_time = '%.0f' % (time.time() * 10 ** 7)
        picture_name = request.user.username + '-' + now_time + '.jpg'
        if 'cover_img' in request.FILES:
            cover_img = request.FILES['cover_img']
            upload_path = settings.COVER_IMG_PATH + os.path.sep + picture_name

            with open(upload_path, 'wb') as pic:
                for c in cover_img.chunks():
                    pic.write(c)
            upload_url = settings.STATIC_URL + 'cover_img/' + picture_name
        else:
            upload_url = settings.STATIC_URL + 'cover_img/default_cover.png'
        try:
            book = Book.objects.create(book_name=form.cleaned_data['book_name'],
                                       author=form.cleaned_data['author'],
                                       price=form.cleaned_data['price'],
                                       book_num=form.cleaned_data['book_num'],
                                       press=request.POST.get('press', ''),
                                       referee=request.POST.get('referee', ''),
                                       recommended_reasons=request.POST.get('recommended_reasons', ''),
                                       brief_introduction=request.POST.get('brief_introduction', ''),
                                       cover_img_pathname=upload_url)
            print('99999--' + request.POST.get('book_class'))
            add_book_class(request.POST.get('book_class', ''), book)
            book.save()
            data = {'code': error_code.SUCCESS, 'msg': '登记图书成功'}
            return HttpResponse(json.dumps(data))
        except Exception as e:
            print(e)
            data = {'code': error_code.INSERT_ERROR, 'msg': '登记图书失败'}
            return HttpResponse(json.dumps(data))
    else:
        now_time = '%.0f' % (time.time() * 10 ** 7)
        picture_name = request.user.username + '-' + now_time + '.jpg'
        upload_url = ''
        if 'cover_img' in request.FILES:
            cover_img = request.FILES['cover_img']
            upload_path = settings.COVER_IMG_PATH + os.path.sep + picture_name

            with open(upload_path, 'wb') as pic:
                for c in cover_img.chunks():
                    pic.write(c)
            upload_url = settings.STATIC_URL + 'cover_img/' + picture_name

        try:
            book = Book.objects.get(id=request.POST.get('id'))
            book.book_name = form.cleaned_data['book_name']
            book.author = form.cleaned_data['author']
            book.price = form.cleaned_data['price']
            book.book_num = form.cleaned_data['book_num']
            book.press = request.POST.get('press', '')
            book.referee = request.POST.get('referee', '')
            book.recommended_reasons = request.POST.get('recommended_reasons', '')
            book.brief_introduction = request.POST.get('brief_introduction', '')
            if upload_url == '':
                book.cover_img_pathname = book.cover_img_pathname
            else:
                book.cover_img_pathname = upload_url
            add_book_class(request.POST.get('book_class', ''), book)
            book.save()

            data = {'code': error_code.SUCCESS, 'msg': '修改图书成功'}
            return HttpResponse(json.dumps(data))
        except Exception:
            data = {'code': error_code.UPDATE_ERROR, 'msg': '修改图书失败'}
            return HttpResponse(json.dumps(data))


def add_book_class(book_class_ids, book):
    if book_class_ids != '':
        book_class_ids = book_class_ids.split(';')
        for book_class_id in book_class_ids:
            book_class_id = book_class_id.split('/')
            main_class_id = book_class_id[0]
            child_class_id = book_class_id[1]
            class_id = child_class_id if child_class_id != '-1' else main_class_id
            book_class = BookClass.objects.filter(id=class_id)
            if len(book_class) != 1:
                data = {'code': error_code.DATA_ABNORMAL, 'msg': '图书类别有误'}
                return HttpResponse(json.dumps(data))
            book.bookclass_set.add(book_class[0])


def form_book_class_str(book):
    book_class_list = []
    for book_class in book.bookclass_set.all():
        if book_class.parent_id == 0:
            book_class_list.append(book_class.name + '/无')
        else:
            main_class = BookClass.objects.filter(id=book_class.parent_id)
            if len(main_class) != 1:
                continue
            book_class_list.append(main_class[0].name + '/' + book_class.name)
    return book_class_list


# 图书详细信息
@login_required(login_url='login:login')
@require_GET
def book_detailed_info(request, book_id):
    book = Book.objects.get(id=book_id)
    book_class = form_book_class_str(book)

    return render(request, 'book_detail_info.html', {
        'book_detail_info': book,
        'book_class_list': book_class
    })


# 借阅图书
@login_required(login_url='login:login')
@csrf_exempt
@require_POST
def book_borrowing(request):
    book_id = request.POST.get('book_id', '')
    if book_id == '':
        data = {'code': error_code.BOOK_BORROW_ERROR, 'msg': '图书借阅失败'}
        return HttpResponse(json.dumps(data))
    else:
        book = Book.objects.get(id=book_id)
        if book.book_num == book.borrow_num:
            data = {'code': error_code.BOOK_HAS_BEEN_BORROW, 'msg': '图书已被借阅'}
            return HttpResponse(json.dumps(data))
        else:
            book_borrow_count = BookBorrowItem.objects.filter(book_name=book.book_name,
                                                              borrower=request.user.first_name).count()
            if book_borrow_count > 0:
                data = {'code': error_code.BOOK_ALREADY_BORROW, 'msg': '您已借阅此书'}
                return HttpResponse(json.dumps(data))

            user = request.user
            if user.userprofile.center == '领导':
                borrower_center_department = user.userprofile.center
            else:
                borrower_center_department = user.userprofile.center + '-' + user.userprofile.department
            book.borrow_num = book.borrow_num + 1

            end_time = datetime.datetime.now() + datetime.timedelta(days=30)
            book_borrow_item = BookBorrowItem.objects.create(book_name=book.book_name,
                                                             borrower=user.first_name,
                                                             borrower_department=borrower_center_department,
                                                             borrowed_time=datetime.datetime.now(),
                                                             end_time=end_time)
            book.save()
            book_borrow_item.save()
            data = {'code': error_code.BOOK_BORROW_SUCCESS, 'msg': '借阅成功'}
            return HttpResponse(json.dumps(data))


# 续借图书
@login_required(login_url='login:login')
@csrf_exempt
@require_POST
def renew_book(request):
    borrow_item_id = request.POST.get('borrow_id', '')
    if borrow_item_id == '':
        data = {'code': error_code.BOOK_RENEW_ERROR, 'msg': '续借失败'}
        return HttpResponse(json.dumps(data))
    else:
        borrow_item = BookBorrowItem.objects.get(id=borrow_item_id)
        if datetime.datetime.now() < borrow_item.end_time - datetime.timedelta(days=7):
            data = {'code': error_code.BOOK_DISTANCE_BORROW, 'msg': '请距截止日期7天内续借图书'}
            return HttpResponse(json.dumps(data))
        else:
            borrow_item.end_time = borrow_item.end_time + datetime.timedelta(days=15)
            borrow_item.save()
            data = {'code': error_code.BOOK_RENEW_SUCCESS, 'msg': '续借成功'}
            return HttpResponse(json.dumps(data))


# 编辑图书
@require_GET
@login_required(login_url='login:login')
def update_book_info(request, book_id):
    book = Book.objects.get(id=book_id)
    book_class_list = []
    for book_class in book.bookclass_set.all():
        if book_class.parent_id == 0:
            book_class_list.append(book_class.name + '/无')
        else:
            main_class = BookClass.objects.filter(id=book_class.parent_id)
            if len(main_class) != 1:
                continue
            book_class_list.append(main_class[0].name + '/' + book_class.name)

    book_main_class_list = BookClass.objects.filter(parent_id=0)
    if len(book_main_class_list) == 0:
        return render(request, 'input_book_info.html', {
            'book_main_class_list': [],
            'book_child_class_list': []
        })

    book_child_class_list = BookClass.objects.filter(parent_id=book_main_class_list[0].id)
    return render(request, 'input_book_info.html', {
        'book_info': book,
        'book_class_list': book_class_list,
        'book_main_class_list': list(book_main_class_list),
        'book_child_class_list': list(book_child_class_list)
    })


# 删除图书
@login_required(login_url='login:login')
@csrf_exempt
@require_POST
def delete_book(request):
    book_id = request.POST.get('book_id', '')
    if book_id == '':
        data = {'code': error_code.DELETE_ERROR, 'msg': '删除失败'}
        return HttpResponse(json.dumps(data))
    else:
        books = Book.objects.filter(id=book_id)
        if len(books) != 1:
            data = {'code': error_code.DATA_ABNORMAL, 'msg': '图书数据异常'}
            return HttpResponse(json.dumps(data))

        book = books[0]
        if book.borrow_num != 0:
            data = {'code': error_code.BOOK_EXIST_BORROW, 'msg': '此图书尚有借出部分，无法删除'}
            return HttpResponse(json.dumps(data))

        cover_img = book.cover_img_pathname
        book.delete()

        cover_img_path = settings.BASE_DIR + cover_img
        if os.path.exists(cover_img_path):
            os.remove(cover_img_path)

        data = {'code': error_code.DELETE_ERROR, 'msg': '删除成功'}
        return HttpResponse(json.dumps(data))


# 借阅记录
@login_required(login_url='login:login')
@require_GET
def book_borrow_items(request):
    user = request.user
    my_borrow_item = BookBorrowItem.objects.filter(borrower=user.first_name)
    all_borrow_item = BookBorrowItem.objects.all()
    return render(request, 'borrow_record.html', {
        'user': user,
        'my_borrow_item': my_borrow_item,
        'all_borrow_item': all_borrow_item
    })


# 历史借阅记录
@login_required(login_url='login:login')
@require_GET
def borrow_history(request):
    all_borrow_history = BookBorrowHistory.objects.all()
    return render(request, 'borrow_history.html', {
        'all_borrow_history': all_borrow_history,
    })


# 还书
@login_required(login_url='login:login')
@csrf_exempt
@require_POST
def return_book(request):
    borrow_item_id = request.POST.get('borrow_item_id', '')
    if borrow_item_id == '':
        return HttpResponse(json.dumps({'code': error_code.RETURN_BOOK_ERROR, 'msg': '还书失败'}))
    else:
        book_borrow_item = BookBorrowItem.objects.get(id=borrow_item_id)
        book = Book.objects.get(book_name=book_borrow_item.book_name)
        book_borrow_history = BookBorrowHistory.objects.create(book_name=book_borrow_item.book_name,
                                                               borrower=book_borrow_item.borrower,
                                                               borrower_department=book_borrow_item.borrower_department,
                                                               borrowed_time=book_borrow_item.borrowed_time,
                                                               book_return_time=datetime.datetime.now())
        book_borrow_history.save()

        BookBorrowItem.objects.filter(id=borrow_item_id).delete()

        book.borrow_num = book.borrow_num - 1
        book.save()

        return HttpResponse(json.dumps({'code': error_code.RETURN_BOOK_SUCCESS, 'msg': '还书成功'}))


# 跳转图书类型页
@require_GET
def jump_class_tree(request):
    return render(request, 'input_book_class.html')


# 图书类型数据
@login_required(login_url='login:login')
@require_GET
def book_class_tree(request):
    book_class_tree_list = BookClass.objects.values('id', 'parent_id', 'name')
    return HttpResponse(json.dumps(list(book_class_tree_list), ensure_ascii=False))


# 根据parent_id获取图书类型
@login_required(login_url='login:login')
@require_GET
def find_book_class_parent(request):
    parent_id = request.GET.get('parent_id')
    book_class_list = BookClass.objects.values('id', 'parent_id', 'name').filter(parent_id=parent_id)
    data = {'book_class': list(book_class_list)}
    return HttpResponse(json.dumps(data))


# 添加一级图书类型
@login_required(login_url='login:login')
@csrf_exempt
@require_POST
def input_book_class(request):
    parent_id = request.POST.get('parent_id', '')
    book_class_name = request.POST.get('name', '')
    if parent_id == '' or book_class_name == '':
        data = {'code': error_code.INSERT_ERROR, 'msg': '添加图书类型失败'}
        return HttpResponse(json.dumps(data))
    else:
        main_book_class = BookClass.objects.filter(name=book_class_name, parent_id=0)
        if len(main_book_class) != 0:
            data = {'code': error_code.BOOK_CLASS_EXIST, 'msg': '已添加该图书主类型'}
            return HttpResponse(json.dumps(data))
        else:
            book_class = BookClass.objects.create(name=book_class_name, parent_id=parent_id)
            book_class.save()
            data = {'code': error_code.SUCCESS, 'msg': '添加图书类型成功'}
            return HttpResponse(json.dumps(data))


# 删除图书类型
@login_required(login_url='login:login')
@csrf_exempt
@require_POST
def del_book_class(request):
    book_class_id = request.POST.get('book_class_id', '')
    if book_class_id == '':
        data = {'code': error_code.DELETE_ERROR, 'msg': '删除图书类型失败'}
        return HttpResponse(json.dumps(data))
    else:
        book_type = BookClass.objects.get(id=book_class_id)
        if book_type.parent_id == 0:
            BookClass.objects.filter(parent_id=book_class_id).delete()
        BookClass.objects.filter(id=book_class_id).delete()
        data = {'code': error_code.SUCCESS, 'msg': '删除图书类型成功'}
        return HttpResponse(json.dumps(data))


# 修改图书类型
@login_required(login_url='login:login')
@csrf_exempt
@require_POST
def update_book_class(request):
    book_class_id = request.POST.get('book_class_id', '')
    parent_id = request.POST.get('parent_id', '')
    book_class_name = request.POST.get('name', '')
    if book_class_id == '' or parent_id == '' or book_class_name == '':
        data = {'code': error_code.UPDATE_ERROR, 'msg': '修改图书类型失败'}
        return HttpResponse(json.dumps(data))
    else:
        book_type = BookClass.objects.filter(name=book_class_name)
        book_class = BookClass.objects.get(id=book_class_id)
        if book_type and book_class.parent_id == 0:
            data = {'code': error_code.BOOK_CLASS_EXIST, 'msg': '已有该图书类型,请重新修改图书类型'}
            return HttpResponse(json.dumps(data))
        else:
            book_class.parent_id = parent_id
            book_class.name = book_class_name
            book_class.save()

            data = {'code': error_code.SUCCESS, 'msg': '修改图书类型成功'}
            return HttpResponse(json.dumps(data))


# 导出历史借阅记录
@require_GET
@login_required(login_url='login:login')
def expert_borrow_history(request):
    find_history_sql = '''
                          SELECT * FROM book_borrow_bookborrowhistory \
                          WHERE DATE_FORMAT( book_return_time, '%Y%m' ) = DATE_FORMAT( CURDATE( ) , '%Y%m' )
                       '''
    host = settings.DATABASES['default']['HOST']
    port = settings.DATABASES['default']['PORT']
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    db = settings.DATABASES['default']['NAME']

    path_name = settings.BASE_DIR + os.path.sep + 'borrow_history.xlsx'

    conn = pymysql.connect(host=host, port=int(port), user=user, passwd=password, db=db, charset='utf8')
    try:
        a = pd.read_sql(find_history_sql, conn)
    except:
        return HttpResponse()
    finally:
        conn.close()

    a['书名'] = a.book_name

    a['借阅人'] = a.borrower

    a['部门'] = a.borrower_department

    borrowed_time = []
    for t in a.borrowed_time:
        borrowed_time.append(t.strftime('%Y-%m-%d %H:%M:%S'))

    a['借阅时间'] = borrowed_time

    book_return_time = []
    for t in a.book_return_time:
        book_return_time.append(t.strftime('%Y-%m-%d %H:%M:%S'))

    a['还书时间'] = book_return_time

    a.to_excel(path_name, index=False, columns=['书名', '借阅人', '部门', '借阅时间', '还书时间'])

    file = open(path_name, 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="borrow_history.xlsx"'
    return response


# 导出导出库存图书
@require_GET
@login_required(login_url='login:login')
def expert_stock_book(request):
    find_stock_sql = '''
                        select book_name, book_num-borrow_num as stock_num from book_borrow_book \
                        where book_num-borrow_num != 0
                     '''
    host = settings.DATABASES['default']['HOST']
    port = settings.DATABASES['default']['PORT']
    user = settings.DATABASES['default']['USER']
    password = settings.DATABASES['default']['PASSWORD']
    db = settings.DATABASES['default']['NAME']

    path_name = settings.BASE_DIR + os.path.sep + 'stock_book.xlsx'

    conn = pymysql.connect(host=host, port=int(port), user=user, passwd=password, db=db, charset='utf8')
    try:
        a = pd.read_sql(find_stock_sql, conn)
    except:
        return HttpResponse()
    finally:
        conn.close()

    a['书名'] = a.book_name

    a['库存数量'] = a.stock_num

    a.to_excel(path_name, index=False, columns=['书名', '库存数量'])

    file = open(path_name, 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="stock_book.xlsx"'
    return response


@require_GET
@login_required(login_url='login:login')
def user_manage(request):
    user_profiles = UserProfile.objects.all()
    groups = Group.objects.all()
    permissions = []
    for group in groups:
        if group.name == '管理员':
            permissions.insert(0, group)
        else:
            permissions.append(group)
    return render(request, "user_manage.html", {
        "user_profiles": reversed(user_profiles),
        "permission_list": permissions
    })


@require_POST
@csrf_exempt
@login_required(login_url='login:login')
def add_user(request):
    username = request.POST.get("username", "")
    user = User.objects.filter(username=username)
    if len(user) != 0:
        data = {'code': error_code.USER_EXIST, 'msg': '用户已存在'}
        return HttpResponse(json.dumps(data))

    fullname = request.POST.get("fullname", "")
    center = request.POST.get("center", "")
    department = request.POST.get("department", "")
    position = request.POST.get("position", "")
    group_id = request.POST.get("permission", "")
    if username == "" or fullname == "" or \
       center == "" or department == "" or position == "":
        data = {'code': error_code.USER_INFO_NOT_COMPLETE, 'msg': '用户信息不完整'}
        return HttpResponse(json.dumps(data))

    new_user = User.objects.create(username=username,
                                   first_name=fullname)
    new_user_profile = UserProfile.objects.create(user=new_user,
                                                  center=center,
                                                  department=department,
                                                  position=position)
    group = Group.objects.filter(id=group_id)
    if len(group) != 1:
        data = {'code': error_code.DATA_ABNORMAL, 'msg': '用户组数据异常'}
        return HttpResponse(json.dumps(data))
    new_user.groups.add(group[0])
    new_user_profile.save()

    new_user.set_password("sxfs123456")
    new_user.save()

    data = {'code': 200, error_code.SUCCESS: '添加用户成功'}
    return HttpResponse(json.dumps(data))


@require_POST
@csrf_exempt
@login_required(login_url='login:login')
def delete_user(request):
    username = request.POST.get("username", "")
    if username == request.user.username:
        data = {'code': error_code.USER_CANNOT_DELETE, 'msg': '不能删除本用户'}
        return HttpResponse(json.dumps(data))

    user = User.objects.filter(username=username)
    if len(user) == 0:
        data = {'code': error_code.USER_NOT_EXIST, 'msg': '该用户不存在'}
        return HttpResponse(json.dumps(data))

    if len(user) > 1:
        data = {'code': error_code.DATA_ABNORMAL, 'msg': '用户信息异常'}
        return HttpResponse(json.dumps(data))

    user[0].delete()

    data = {'code': error_code.SUCCESS,  'msg': '删除用户成功'}
    return HttpResponse(json.dumps(data))
