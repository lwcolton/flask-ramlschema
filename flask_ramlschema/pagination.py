import math

from flask import request
import pymongo

from .errors import InvalidPageError

def get_page(find_cursor, page_request=None):
    if page_request is None:
        page_request = request
    page_num, per_page, sort_by, order, order_arg = get_pagination_args(page_request)
    page = create_page(find_cursor, page_num, per_page, sort_by, order, order_arg)
    return page

def create_page(self, items, page_num, per_page, order, items_key="sorted"):
    """Slices items to create a page.

    Args:
        items (list): List of items to paginate
        page_num (int): Number of page to return
        per_page (int): Number of items per page
        order (string): One of 'ascending', 'descending'
        items_key (string): Key in the return object which maps to the list of items.
    """
    total_entries = len(items)
    page_wrapper = {}
    page_wrapper["page"] = page_num
    page_wrapper["per_page"] = per_page
    total_pages = int(math.ceil(total_entries / float(page_wrapper["per_page"])))
    if total_pages == 0:
        total_pages = 1
    page_wrapper["total_pages"] = total_pages
    page_wrapper["total_entries"] = total_entries
    page_wrapper["order"] = order
    if page_num > page_wrapper["total_pages"] or page < 1:
        raise InvalidPageError(page_num)
    page_start = per_page*(page_num-1)
    page_end = page_start + per_page
    if order == "descending":
        # http://stackoverflow.com/questions/3705670/best-way-to-create-a-reversed-list-in-python
        page_items = items[::-1][page_start:page_end]
    else:
        page_items = items[page_start:page_end]
    page_wrapper[items_key] = page_items
    return page_wrapper

def get_pagination_args(request, max_per_page=100):
    page_num = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))
    if per_page > max_per_page:
        raise ValueError("per_page cannot be greated than 100")

    sort_by = request.args.get("sort_by", "id")
    if sort_by == "id":
        sort_by = "_id"

    # order values based on backbone-paginator
    order_arg = request.args.get("order", 1)
    if order_arg == 1:
        order = pymongo.DESCENDING
    else:
        order = pymongo.ASCENDING

    return page_num, per_page, sort_by, order, order_arg
