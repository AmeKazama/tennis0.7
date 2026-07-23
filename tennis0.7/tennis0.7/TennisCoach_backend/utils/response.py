from fastapi.responses import JSONResponse


def success(data=None, message="成功", **extra):
    content = {
        "code": 200,
        "message": message,
        "data": data,
    }
    content.update(extra)
    return JSONResponse(
        status_code=200,
        content=content,
    )


def error(message="失败", code=400):
    return JSONResponse(
        status_code=code,
        content={
            "code": code,
            "message": message,
            "data": None,
        },
    )
