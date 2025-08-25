from ninja import Router


v2 = Router()


@v2.get("/greetings")
def greetings(request):
    return {"message": "Hello, World! v2"}
