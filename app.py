import os
import streamlit as st
from google import genai
# Note: types 모듈을 직접 임포트 할 필요가 줄어들었습니다!

# 🚨 Streamlit Secrets에서 API 키를 가져오는 로직 (권장)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"] 
except (FileNotFoundError, KeyError):
    # 로컬 테스트 시 환경 변수 사용
    API_KEY = os.environ.get("GEMINI_API_KEY")

# ... (API_KEY 설정 부분은 그대로 유지) ...

# 사용할 모델 설정
MODEL = 'gemini-2.5-flash'

# 0. 시스템 프롬프트 정의 (새로 추가)
SYSTEM_PROMPT = """
당신은 세계적으로 인정받는 **예술 전문가**입니다. 
당신은 예술사, 미술 기법, 현대 예술 트렌드에 대한 깊이 있는 지식을 가지고 있습니다.
사용자의 질문에 대해 깊이 있는 예술적 통찰력과 역사적 맥락을 바탕으로 친절하고 전문가답게 답변해야 합니다.
답변은 항상 한국어로 제공하며, 명확하고 이해하기 쉽게 설명해 주세요.
"""
# ----------------------------------

# 1. Gemini 클라이언트 초기화 함수 (수정된 부분)
# @st.cache_resource를 사용하여 이 함수는 딱 한 번만 실행됩니다.
@st.cache_resource
def get_gemini_client(api_key):
    """Gemini 클라이언트를 한 번만 생성하여 반환합니다."""
    st.info("Gemini 클라이언트 초기화 중...") # 초기화 시에만 이 메시지가 보입니다.
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Gemini 클라이언트 초기화 오류: {e}")
        st.stop()

# 클라이언트 객체를 캐시된 함수를 통해 가져옵니다.
if not API_KEY:
    st.error("Gemini API Key를 찾을 수 없습니다. Streamlit Secrets 또는 환경 변수에 키를 설정해주세요.")
    st.stop()
    
# 캐시된 클라이언트 사용
client = get_gemini_client(API_KEY)


## --- 챗봇 세션 관리 (client.chats 사용) --- ##
# ... (나머지 코드는 그대로 유지) ...
## --- 챗봇 세션 관리 (client.chats 사용) --- ##

st.title("✨ Streamlit 챗봇 (맥락 기억 가능)")
st.markdown("Gemini API의 `Chat Service`를 사용하여 대화 기록을 유지합니다.")

# 2. 채팅 세션 초기화
# 세션 상태에 'chat' 객체가 없으면 새로 생성합니다.
# 2. 채팅 세션 초기화 (기존 코드와 동일, Chat 객체는 캐시될 수 없습니다.)

if "chat" not in st.session_state:
    #if "chat" not in st.session_state:
    # system_instruction 없이 채팅 세션을 생성합니다.
    st.session_state.chat = client.chats.create(model=MODEL)
    st.session_state.messages = []
    
    # 🌟 첫 번째 메시지로 시스템 프롬프트를 주입합니다. (User 역할)
    # 모델에게 인격을 부여하는 메시지를 먼저 보냅니다.
    initial_prompt = f"당신은 이제부터 다음 지침에 따라 답변해야 합니다: {SYSTEM_PROMPT}"
    
    # 이 첫 번째 메시지는 사용자에게 표시되지 않고, 대화 기록에만 추가됩니다.
    st.session_state.chat.send_message(initial_prompt)
    
    # 사용자에게는 인격이 부여되었다는 메시지를 보여줄 수 있습니다.
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! 저는 이제부터 **예술 전문가**로서 질문에 답변해 드릴게요."})


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

    # 5. Gemini Chat Service를 사용하여 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            try:
                # chat.send_message()를 호출하면, Gemini가 이전 대화 기록을 자동으로 참조합니다.
                response = st.session_state.chat.send_message(prompt)
                
                # 응답을 화면에 표시
                st.markdown(response.text)
                
                # 6. 응답을 세션 기록에 저장
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"API 호출 중 오류가 발생했습니다: {e}")
