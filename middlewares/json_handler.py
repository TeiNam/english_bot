# middlewares/json_handler.py
from fastapi import Request
import json


async def raw_json_middleware(request: Request, call_next):
    """raw 데이터를 처리하는 미들웨어"""
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            # 원본 데이터 읽기
            body = await request.body()
            if body:
                # 바이트를 문자열로 변환
                raw_str = body.decode()

                # JSON 파싱을 시도
                try:
                    # 먼저 있는 그대로 파싱 시도
                    json.loads(raw_str)
                except json.JSONDecodeError:
                    # 파싱 실패 시 문자열 처리
                    # 1. 연속된 큰따옴표 처리
                    processed = raw_str.replace('""', r'\"')

                    # 2. 작은따옴표 내의 큰따옴표 처리
                    in_single_quotes = False
                    final_processed = ""
                    i = 0

                    while i < len(processed):
                        char = processed[i]
                        if char == "'":
                            in_single_quotes = not in_single_quotes
                        elif char == '"' and in_single_quotes:
                            final_processed += r'\"'
                            i += 1
                            continue
                        final_processed += char
                        i += 1

                    # 처리된 데이터로 요청 수정
                    async def receive():
                        return {
                            "type": "http.request",
                            "body": final_processed.encode()
                        }

                    request._receive = receive

        except Exception as e:
            print(f"Middleware error: {str(e)}")

    response = await call_next(request)
    return response