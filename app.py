import os
import streamlit as st
from google import genai
from google.genai import types

# 🚨 주의: 실제 배포 시에는 st.secrets를 사용해야 합니다.
# 로컬 테스트를 위해 환경 변수에서 API 키를 가져옵니다.
# 배포할 때는 아래 # 주석 처리된 라인을 사용하세요!
try:
    # 🌟 Streamlit Cloud 배포 시: st.secrets에서 API 키를 가져옴
    API_KEY = st.secrets["GEMINI_API_KEY"] 
except (FileNotFoundError, KeyError):
    # 🖥️ 로컬 테스트 시: 환경 변수에서 API 키를 가져옴
    API_KEY = os.environ.get("GEMINI_API_KEY")

# 1. Gemini 클라이언트 초기화
if not API_KEY:
    st.error("Gemini API Key를 찾을 수 없습니다. 환경 변수 'GEMINI_API_KEY' 또는 Streamlit Secrets에 키를 설정해주세요.")
    st.stop()

# 클라이언트 초기화
try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"Gemini 클라이언트 초기화 오류: {e}")
    st.stop()

# 사용할 모델 설정
MODEL = 'gemini-2.5-flash' # 빠르고 비용 효율적인 모델

## --- 챗봇 세션 관리 로직 --- ##

st.title("✨ Streamlit 챗봇 with Gemini API")
st.markdown("학교 과제를 위한 간단한 Gemini 챗봇입니다. 질문을 입력해 보세요!")

# 2. 채팅 기록(history) 초기화
# Streamlit의 session_state를 사용하여 대화 기록을 유지합니다.
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Streamlit에 이전 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("여기에 질문을 입력하세요..."):
    # 사용자의 입력 저장 및 화면에 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 5. Gemini API를 사용하여 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            try:
                # 대화 기록을 history 객체로 변환 (Gemini API 형식에 맞게)
                history = [
                    types.Content(
                        role="model" if m["role"] == "assistant" else "user", 
                        parts=[types.Part.from_text(m["content"])]
                    ) for m in st.session_state.messages
                ]
                
                # generate_content 호출 (가장 최근의 프롬프트만 전달)
                # 이 예제에서는 단순하게 가장 최근 프롬프트만 사용합니다.
                # 전체 대화 맥락을 유지하려면, `client.chats`를 사용하는 것이 더 좋습니다.
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt # 대화 기록 대신 현재 프롬프트만 전송
                )
                
                # 응답을 화면에 표시
                st.markdown(response.text)
                
                # 6. 응답을 세션 기록에 저장
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"API 호출 중 오류가 발생했습니다: {e}")
