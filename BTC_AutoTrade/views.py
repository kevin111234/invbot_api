from openai import OpenAI
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
import pyupbit

@login_required
def call_openai(request):
    # 로그인된 사용자 객체에서 API 키 가져오기
    user = request.user
    openai_api_key = user.openai_api_key

    if not openai_api_key:
        return JsonResponse({"error": "API key not found for user."}, status=400)

    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=openai_api_key)

    # Upbit에서 5분봉 데이터 가져오기
    df = pyupbit.get_ohlcv("KRW-BTC", count=288*10, interval="minute5")

    # OpenAI API 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are an expert cryptocurrency trader. Analyze the following 10-day Bitcoin 5-minute candle data and decide whether to Buy, Sell, or Hold."""
            },
            {
                "role": "user",
                "content": df.to_json()
            }
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format="text"
    )

    # 결과 반환
    return JsonResponse({"decision": response.choices[0].message.content})
