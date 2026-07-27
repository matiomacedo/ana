def on_click(event, context):
    return f"click:{event} by {context['user']}"


def on_close(event, context):
    return f"close:{event} by {context['user']}"
