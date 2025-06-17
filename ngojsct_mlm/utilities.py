from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render,redirect
import socket

def pagination(request,data_list,no_of_records):
    paginator = Paginator(data_list, no_of_records)
    
    page = request.GET.get('page')
    try:
        page_object = paginator.page(page)
    except PageNotAnInteger:
        page_object = paginator.page(1)
    except EmptyPage:
        page_object = paginator.page(paginator.num_pages)
     
    return page_object



def table_body_gen(data_list, model,html_table_header):
    # Start building the table body
    table_body = "<tbody><tr>"
    for th in html_table_header:
        table_body += f"<td>{th}</td>"
    table_body += f"<tr>"
    for index, data in enumerate(data_list, start=1):
        table_body += f"<tr><td>{index}</td>"  # Add Serial Number

        for field in model._meta.fields:
            field_name = field.name
            if field_name in ['id', 'created_at', 'updated_at']:
                continue  # Skip these fields
            field_type = field.get_internal_type()

            # Access the field value
            field_value = getattr(data, field_name)

            # Check for the field type and generate the appropriate <td>
            if field_type in ['CharField', 'TextField', 'IntegerField']:
                table_body += f"<td>{field_value}</td>"
            elif field_type in ['FileField', 'ImageField']:
                # Display as image or link if a file exists
                if field_value:
                    table_body += f"<td><img src='/uploads/{field_value}' alt='{field_name}' style='width: 100px; height: auto;'></td>"
                else:
                    table_body += f"<td>No File</td>"
            elif field_type in ['URLField']:
                   table_body += f"<td><a href='/media/{field_value}' >Click</a></td>"

            else:
                # For any other field types, just display the value
                table_body += f"<td>{field_value}</td>"

        table_body += "</tr>"
    
    table_body += "</tbody>"
    return table_body


# def login_req(func):
#     def wrapper(request, *args, **kwargs):
#         # Check if user is logged in by checking session
#         if request.session.get('user_id'):
#             # If logged in, call the original view
#             return func(request, *args, **kwargs)
#         else:
#             # If not logged in, redirect to login page
#             return redirect('/login')
#     return wrapper


def login_req(function):
    def wrapper(request, *args, **kwargs):
        print('request.user.is_authenticated',request.user.is_authenticated)
        if not request.user.is_authenticated:
            return redirect('/login/')
        return function(request, *args, **kwargs)
    return wrapper

def is_connected_to_internet():
    try:
        # Attempt to connect to a known reliable DNS server (Google DNS)
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False