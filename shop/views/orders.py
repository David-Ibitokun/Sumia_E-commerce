"""Order history for the signed in customer."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from shop.services import orders as order_service, pagination


@login_required(login_url='login')
def order_list(request):
    """Every order placed by the signed in customer."""
    orders = order_service.orders_for_user(request.user)
    page_obj, paginator = pagination.paginate_queryset(request, orders)
    return render(
        request,
        'orders/order_list.html',
        {'page_obj': page_obj, 'paginator': paginator, 'orders': page_obj.object_list},
    )


@login_required(login_url='login')
def order_detail(request, order_number):
    """One of the signed in customer's own orders."""
    order = order_service.get_user_order(request.user, order_number)
    return render(
        request,
        'orders/order_detail.html',
        {
            'order': order,
            'order_items': order_service.order_items(order),
        },
    )