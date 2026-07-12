from fastapi.responses import JSONResponse


def success(data=None, message="成功"):
    return JSONResponse(
        status_code=200,
        content={
            "code": 200,
            "message": message,
            "data": data,
        },
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
