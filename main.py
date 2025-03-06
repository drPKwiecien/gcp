import functions_framework

@functions_framework.http
def hello_world(request):
    request_json = request.get_json()
    if request_json and 'name' in request_json:
        name = request_json['name']
    else:
        name = 'World'
    return f'Hello, {name}!'