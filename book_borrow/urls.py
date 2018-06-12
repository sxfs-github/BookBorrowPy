"""BookBorrowPy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views


app_name = 'book_borrow'
urlpatterns = [
    path('', views.index, name='index'),
    path('book_lists/', views.book_lists, name='book_lists'),
    path('input_book_info/', views.input_book_info, name='input_book_info'),
    path('update_child_class/<str:main_class_id>/', views.update_child_class, name='update_child_class'),
    path('commit_book_info', views.commit_book_info, name='commit_book_info'),
    path('book_detailed_info/<int:book_id>', views.book_detailed_info, name='book_detailed_info'),
    path('book_borrowing/', views.book_borrowing, name='book_borrowing'),
    path('renew_book/', views.renew_book, name='renew_book'),
    path('delete_book/', views.delete_book, name='delete_book'),
    path('return_book/', views.return_book, name='return_book'),
    path('book_borrow_items/', views.book_borrow_items, name='book_borrow_items'),
    path('borrow_history/', views.borrow_history, name='borrow_history'),
    path('book_class_tree/', views.book_class_tree, name='book_class_tree'),
    path('jump_class_tree/', views.jump_class_tree, name='jump_class_tree'),
    path('input_book_class/', views.input_book_class, name='input_book_class'),
    path('find_book_class_parent/', views.find_book_class_parent, name='find_book_class_parent'),
    path('del_book_class/', views.del_book_class, name='del_book_class'),
    path('update_book_class/', views.update_book_class, name='update_book_class'),
    path('expert_borrow_history/', views.expert_borrow_history, name='expert_borrow_history'),
    path('expert_stock_book/', views.expert_stock_book, name='expert_stock_book'),
    path('update_book_info/<int:book_id>', views.update_book_info, name='update_book_info'),
    path('user_manage/', views.user_manage, name='user_manage'),
    path('add_user/', views.add_user, name='add_user'),
    path('delete_user/', views.delete_user, name='delete_user'),
]
