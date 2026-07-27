from handlers import on_click, on_close

HANDLERS = {"click": on_click, "close": on_close}


def dispatch(name, event, context):
    return f"{HANDLERS[name](event)} by {context['user']}"
