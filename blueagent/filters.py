import json


filters = {

}


# Bootstrap
def bootstrap():
    register_filter('contains_text', contains_text)
    register_filter('is_product', is_product)
    register_filter('price_under', price_under)


# Global filter functions
def parse_args(args):

    return args


def register_filter(name, filter):
    filters[name] = filter

    return True


# Filters
def contains_text(item, args):
    args = parse_args(args)

    if args['text'] in item.title.lower():
        return True

    if args['text'] in item.description.lower():
        return True

    return False


def is_product(item, args):
    args = parse_args(args)

    for data in item.item_data:
        if 'Produkt' in data:
            if data['Produkt'].lower() == args['product'].lower():
                return True

    return False


def price_under(item, args):
    args = parse_args(args)

    if item.price <= int(args['price']):
        return True

    return False


def price_over(item, args):
    args = parse_args(args)

    if item.price >= int(args['price']):
        return True

    return False


bootstrap()
