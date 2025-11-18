import os
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# 1. 인격(페르소나) 정의
PERSONAS = {
    "선택 안 함 (일반 챗봇)": "",
    "✨ 예술 전문가": """
        당신은 세계적으로 인정받는 **예술 전문가**입니다. 
        사용자의 질문에 대해 깊이 있는 예술적 통찰력과 역사적 맥락을 바탕으로 친절하고 전문가답게 답변해야 합니다.
        답변의 어조는 교양 있고 품위 있게 유지합니다.
    """,
    "📈 금융 전문가": """
        당신은 금융 시장, 투자, 경제 동향에 해박한 **금융 전문가**입니다.
        사용자에게는 항상 신뢰할 수 있는 정보를 바탕으로, 복잡한 내용을 명확하고 분석적인 시각으로 설명해야 합니다.
        답변 시에는 '위험 분산'이나 '시장 변동성'과 같은 전문 용어를 적절히 사용합니다.
    """,
    "💻 코딩 마스터": """
        당신은 모든 프로그래밍 언어와 알고리즘에 능통한 **코딩 마스터**입니다.
        사용자의 질문에 대해 효율적이고 정확한 코드 예시와 함께 논리적으로 설명해야 합니다.
        답변은 기술적이고 명료하게 구성합니다.
    """
}

# 모델 및 API 키 설정 (이전과 동일)
MODEL = 'gemini-2.5-flash'
try:
    API_KEY = st.secrets["GEMINI_API_KEY"] 
except (FileNotFoundError, KeyError):
    API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("Gemini API Key를 찾을 수 없습니다. 키를 설정해주세요.")
    st.stop()

# 2. 클라이언트 캐싱 (리소스 재사용)
@st.cache_resource
def get_gemini_client(api_key):
    """Gemini 클라이언트를 한 번만 생성하여 반환합니다."""
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Gemini 클라이언트 초기화 오류: {e}")
        st.stop()

client = get_gemini_client(API_KEY)


# 3. 채팅 세션 및 기록 초기화 함수
def reset_chat(client, model, persona_name, persona_prompt):
    """선택된 인격에 따라 채팅 세션과 기록을 재설정합니다."""
    
    # 1. 기존 메시지 기록과 채팅 세션 초기화
    st.session_state.messages = []
    
    # 2. 새로운 채팅 세션 생성
    st.session_state.chat = client.chats.create(model=model)
    
    # 3. 시스템 프롬프트 주입 (인격 부여)
    if persona_prompt:
        # 모델에게 인격을 부여하는 지침을 첫 메시지로 보냅니다. (API 통신)
        initial_instruction = f"당신은 이제부터 **{persona_name}**의 역할로서 다음 지침에 따라 답변해야 합니다: {persona_prompt} 답변은 항상 한국어로 제공하며, 명확하고 이해하기 쉽게 설명해 주세요."
        st.session_state.chat.send_message(initial_instruction)
        
        # 사용자에게 보여줄 환영 메시지를 메시지 기록에 추가합니다.
        st.session_state.messages.append({"role": "assistant", "content": f"안녕하세요! 이제 **{persona_name}**으로서 질문에 답변해 드릴게요. 무엇이 궁금하신가요?"})
    else:
        # 일반 챗봇 환영 메시지
        st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! 저는 Gemini 기반 챗봇입니다. 어떤 도움이 필요하신가요?"})


## --- Streamlit UI 및 로직 --- ##

st.title("🎭 인격 부여 챗봇 앱")
st.markdown("원하는 전문가 역할을 선택하고 질문해 보세요!")

# 4. 인격 선택 Selectbox (Side bar에 배치)
selected_persona_name = st.sidebar.selectbox(
    "💬 챗봇 역할 선택:",
    options=list(PERSONAS.keys()),
    key="persona_selector"
)
current_persona_prompt = PERSONAS[selected_persona_name]


# 5. 채팅 세션 초기화 및 인격 변경 감지
# 'chat' 세션 상태가 없거나, 선택된 인격이 이전과 다르면 초기화 함수를 실행합니다.
if "chat" not in st.session_state or st.session_state.get("last_persona") != selected_persona_name:
    
    # 현재 선택된 인격 이름을 저장하여 다음 실행 시 변경되었는지 확인합니다.
    st.session_state.last_persona = selected_persona_name
    
    # 채팅 세션을 재설정하고 새로운 인격을 부여합니다.
    reset_chat(client, MODEL, selected_persona_name, current_persona_prompt)


# 6. Streamlit에 이전 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. 사용자 입력 처리
if prompt := st.chat_input("여기에 질문을 입력하세요..."):
    # 사용자의 입력 저장 및 화면에 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 8. Gemini Chat Service를 사용하여 응답 생성
    with st.chat_message("assistant"):
        with st.spinner(f"{selected_persona_name}가 생각 중..."):
            try:
                # chat.send_message()를 호출하여 응답을 받습니다.
                response = st.session_state.chat.send_message(prompt)
                
                # 응답을 화면에 표시
                st.markdown(response.text)
                
                # 9. 응답을 세션 기록에 저장
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except APIError as e:
                # API 오류 시 사용자에게 메시지 표시
                st.error(f"API 호출 중 오류가 발생했습니다: {e}")
            except Exception as e:
                # 기타 오류 처리
                st.error(f"예상치 못한 오류가 발생했습니다: {e}")
