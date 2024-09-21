from django.shortcuts import render

import requests
import datetime
import time
from django.http import JsonResponse
import openai
import os

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

# Upbit에서 10일간의 5분봉 데이터를 가져오는 함수
def get_upbit_candle_data():
    url = "https://api.upbit.com/v1/candles/minutes/5"
    headers = {"Accept": "application/json"}
    market = "KRW-BTC"
    count = 200
    end_time = datetime.datetime.now(datetime.UTC)
    collected_data = []
    
    # 10일간의 5분봉 (총 2880개)
    total_candles = 10 * 24 * (60 // 5)
    
    while len(collected_data) < total_candles:
        params = {
            "market": market,
            "count": count,
            "to": end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            collected_data.extend(data)
            last_candle_time_str = data[-1]['candle_date_time_utc']
            end_time = datetime.datetime.strptime(last_candle_time_str, "%Y-%m-%dT%H:%M:%S")
            end_time = end_time.replace(tzinfo=datetime.timezone.utc)
            time.sleep(0.2)  # API rate limit
        else:
            return None
    
    return collected_data[:total_candles]

# 데이터를 JSON으로 응답하는 Django view
def fetch_upbit_data(request):
    data = get_upbit_candle_data()
    if data:
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch data"}, status=500)

# OpenAI API로 데이터를 전송하고 응답 받기
def analyze_with_openai(data):
    prompt = (
        "You are an expert cryptocurrency trader. Analyze the following Bitcoin 5-minute candle data "
        "and decide whether to Buy, Sell, or Hold based on the trends and technical indicators. "
        "Please return your decision in JSON format with an explanation. "
        f"Data: {data}"
    )
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500
        )
        
        # OpenAI의 응답을 JSON으로 파싱
        decision_data = response.choices[0].text.strip()
        return decision_data
    except Exception as e:
        return {"error": str(e)}

# 데이터를 분석하고 매매 결정을 내리는 view
def analyze_data_and_trade(request):
    upbit_data = get_upbit_candle_data()
    
    if upbit_data:
        openai_response = analyze_with_openai(upbit_data)
        return JsonResponse(openai_response, safe=False)
    else:
        return JsonResponse({"error": "Failed to fetch Upbit data"}, status=500)

# 자동 매매 로직 (매수, 매도)
def execute_trade(decision):
    if decision == "Buy":
        # 매수 로직 (Upbit API로 주문 구현)
        print("Executing Buy Order")
    elif decision == "Sell":
        # 매도 로직 (Upbit API로 주문 구현)
        print("Executing Sell Order")
    else:
        # 보류
        print("Holding Position")

# OpenAI API 응답을 바탕으로 자동매매 실행 view
def auto_trade(request):
    upbit_data = get_upbit_candle_data()
    
    if upbit_data:
        openai_response = analyze_with_openai(upbit_data)
        
        # 응답에서 결정을 가져와 자동매매 실행
        try:
            decision = openai_response.get('decision', 'Hold')
            execute_trade(decision)
            return JsonResponse({"decision": decision}, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Failed to fetch Upbit data"}, status=500)
