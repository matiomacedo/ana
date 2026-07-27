from handlers import on_click, on_close

HANDLERS = {"click": on_click, "close": on_close}


def dispatch(name, event):
    return HANDLERS[name](event)
