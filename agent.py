def call_gemini_api(api_key, prompt):
    """💡 v1 정식 스펙에 맞춰 변수명을 response_mime_type으로 완벽 교정"""
    host = "generativelanguage.googleapis.com"
    endpoint = f"/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            # 🔑 [최종 솔루션] v1 API의 표준 스펙인 언더바(_) 표기법으로 수정했습니다.
            "response_mime_type": "application/json",
            "temperature": 0.7
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    conn = http.client.HTTPSConnection(host)
    conn.request("POST", endpoint, body=json.dumps(payload), headers=headers)
    response = conn.getcall = conn.getresponse()
    res_data = response.read().decode('utf-8')
    conn.close()
    
    res_json = json.loads(res_data)
    
    if 'candidates' not in res_json:
        print(f"❌ 구글 API 원본 반환 에러 구조: {res_json}")
        raise KeyError("구글 제미나이가 정상적인 답변 구조를 생성하지 못했습니다. 원본 로그를 확인하세요.")
        
    text_response = res_json['candidates'][0]['content']['parts'][0]['text']
    return text_response
