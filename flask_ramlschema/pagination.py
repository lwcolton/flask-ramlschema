import math

import pymongo


def get_pagination_wrapper(find_cursor, page, per_page, sort_by, order, order_arg):
    total_entries = find_cursor.count()
    page_wrapper = {}
    page_wrapper["page"] = page
    page_wrapper["per_page"] = per_page
    page_wrapper["total_pages"] = int(math.ceil(total_entries / float(page_wrapper["per_page"])))
    page_wrapper["total_entries"] = total_entries
    page_wrapper["sort_by"] = sort_by
    page_wrapper["order"] = order_arg

    if page_wrapper["page"] > page_wrapper["total_pages"] or page_wrapper["page"] < 1:
        if total_entries != 0 or page_wrapper["page"] != 1:
            raise ValueError("invalid page number: {0]".format(page_wrapper["page"]))
    skip_num = per_page*(page-1)
    find_cursor.sort(sort_by, order).skip(skip_num).limit(per_page)
    items = list(find_cursor)
    for mongo_doc in items:
        mongo_doc["id"] = mongo_doc["_id"]
        del mongo_doc["_id"]
    page_wrapper["items"] = items
    return page_wrapper

def get_pagination_args(request, max_per_page=100):
    page = int(request.args.get("page", 1))
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

    return page, per_page, sort_by, order, order_arg