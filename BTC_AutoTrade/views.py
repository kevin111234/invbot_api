from openai import OpenAI
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
import pyupbit
from user.models import UserProfile
import json

@login_required
def call_openai(request):
    # 로그인된 사용자 객체에서 API 키 가져오기
    user = request.user
    
    # UserProfile에서 해당 사용자의 API 키 가져오기
    try:
        user_profile = UserProfile.objects.get(user=user)  # UserProfile 객체 가져오기
        openai_api_key = user_profile.openai_api_key  # API 키 가져오기
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User profile not found."}, status=400)

    if not openai_api_key:
        return JsonResponse({"error": "API key not found for user."}, status=400)

    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=openai_api_key)

    # Upbit에서 5분봉 데이터 가져오기
    df = pyupbit.get_ohlcv("KRW-BTC", count=288*1, interval="minute5")

    # OpenAI API 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are an expert cryptocurrency trader. Analyze the following 10-day Bitcoin 5-minute candle data and decide whether to Buy, Sell, or Hold based on price trends, momentum, and volatility indicators.
                  Data Format: 
                  [
                      {
                          "timestamp": "YYYY-MM-DD HH:MM:SS",
                          "open": 34000.0,
                          "high": 34150.0,
                          "low": 33900.0,
                          "close": 34050.0,
                          "volume": 120.5
                      },
                      ...
                  ]

                  Your task:
                  1. Analyze the data provided using technical indicators such as RSI, Moving Averages (MA), and Bollinger Bands.
                  2. Consider the recent price trends and volatility to decide the next action (Buy, Sell, Hold).
                  3. Respond with a clear decision (Buy, Sell, or Hold) in only JSON format, without additional formatting or code blocks.
                  4. Include the reason for your decision in the explanation field.
                  5. Also provide a recommended price to execute the action and what percentage of the user's capital should be allocated for this trade.

                  Example Response:
                  {
                    "decision": "Buy",
                    "recommended_price": 34000.0,
                    "capital_allocation": 0.5,
                    "explanation": "The RSI is below 30, indicating oversold conditions, and the price is near the lower Bollinger Band, suggesting a potential reversal."
                  }
                  """
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
        presence_penalty=0
    )

    # 결과 반환
    response_content = response.choices[0].message.content

    try:
        # 응답이 중첩된 JSON 형식이라면 이를 파싱
        parsed_response = json.loads(response_content)  # JSON 문자열 파싱
    except json.JSONDecodeError:
        return JsonResponse({"error": "Failed to parse OpenAI response."}, status=500)

    # 올바른 JSON 형태로 반환
    return JsonResponse(parsed_response)