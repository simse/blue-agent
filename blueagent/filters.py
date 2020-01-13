import json
from blueagent.logger import logger

# Global filter functions
def parse_args(args):
    return args


# Filters
def contains_text(item, args):
    args = parse_args(args)

    if args['text'].lower() in item.title.lower():
        return True

    if args['text'].lower() in item.description.lower():
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


filters = {
    'contains_text': contains_text,
    'is_product': is_product,
    'price_under': price_under,
    'price_over': price_over
}