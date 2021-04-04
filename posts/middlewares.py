class AddContextAttrMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    # noinspection PyMethodMayBeStatic, PyUnusedLocal
    def process_template_response(self, request, response):
        response.context = response.context_data
        return response
