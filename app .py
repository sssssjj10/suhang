"""실행: streamlit run app.py
GitHub에 app.py와 requirements.txt를 올려 Streamlit Community Cloud로 배포하세요.
QR은 배포 주소를 입력하여 생성합니다. 체크 상태는 현재 브라우저 세션에만 보관됩니다.
"""
import io
import json
import re
from urllib.parse import urlsplit

import qrcode
import streamlit as st

st.set_page_config(page_title="아빠의 스마트 낚시 비서", page_icon="🎣", layout="centered", initial_sidebar_state="collapsed")
# 아이콘 폰트까지 덮는 전역 font-family 지정, 헤더 높이 0, 강제 열 압축을 하지 않습니다.
st.markdown("""
<style>
.block-container {max-width:760px;padding-top:3.5rem;padding-bottom:1rem;padding-left:0.8rem;padding-right:0.8rem;}
h3 {margin-bottom:0.3rem;font-size:1.25rem;}
.stButton button {min-height:2.75rem;}
</style>
""", unsafe_allow_html=True)
st.markdown("### 🎣 아빠의 맞춤 출조 비서라용!")
st.caption("바다는 기상 확인, 민물은 자리 문의, 챙길 짐까지 한눈에 확인하세용!")

with st.expander("📱 QR로 앱 열기 · 사용 안내"):
    address = st.text_input("실제 배포한 앱 주소", placeholder="https://내앱.streamlit.app")
    if address:
        try:
            parsed = urlsplit(address.strip())
            port = parsed.port
            valid = parsed.scheme in ("http", "https") and bool(parsed.hostname) and not parsed.username and not parsed.password and not any(c.isspace() for c in address)
        except ValueError:
            valid = False
        if valid:
            data = io.BytesIO()
            qrcode.make(address.strip()).save(data, format="PNG")
            st.image(data.getvalue(), width=200)
            st.download_button("QR 이미지 저장", data.getvalue(), "fishing-qr.png", "image/png")
        else:
            st.warning("http:// 또는 https://로 시작하는 올바른 주소를 입력하세요.")
    st.caption("QR은 앱 접속용이며 체크 결과를 다른 기기와 공유하지 않습니다. 체크 결과는 현재 세션에만 보관됩니다. 다운로드한 준비물 파일은 나중에 불러올 수 있습니다.")
    st.caption("모바일에서 기본 위젯이 자연스럽게 배치됩니다. 작은 화면에서는 내용에 따라 스크롤이 필요합니다.")

tab_sea, tab_fresh, tab_checklist = st.tabs(["🌊 바다 낚시", "🎣 민물 낚시", "📋 준비물 체크"])

with tab_sea:
    st.subheader("🌊 바다 출조 참고 & 배 예약이라용")
    with st.expander("⚠️ 오늘 바다 나가도 될까용?", expanded=True):
        st.caption("실시간 조회가 아닙니다. 출조 해역·시간대의 예보를 확인해 직접 입력하세요.")
        col_s1, col_s2 = st.columns(2)
        wave_height = col_s1.number_input("파도 높이 (m)", min_value=0.0, max_value=30.0, value=None, step=0.1, placeholder="예보 입력")
        wind_speed = col_s2.number_input("풍속 (m/s)", min_value=0.0, max_value=100.0, value=None, step=0.5, placeholder="예보 입력")
        hazard = st.checkbox("특보·낙뢰·너울·출입 통제 등 위험 있음")
        if hazard or (wave_height is not None and wave_height >= 1.5) or (wind_speed is not None and wind_speed >= 8.0):
            st.error("🚨 출조 보류·취소를 우선 검토하세용! 공식 기상과 현장 통제를 확인하세요. 내항으로 이동해도 안전이 보장되지 않습니다.")
        elif wave_height is None or wind_speed is None:
            st.info("파고와 풍속을 모두 입력해 주세요. 입력 전에는 판단하지 않습니다.")
        elif wave_height >= 1.0 or wind_speed >= 6.0:
            st.warning("⚠️ 주의가 필요해용! 선장·관리자에게 확인하고, 공식 기상과 현장 통제를 따르세요.")
        else:
            st.info("입력값은 앱의 주의 기준보다 낮아용. 하지만 안전하다는 뜻은 아닙니다. 너울·조류·돌풍·낙뢰도 확인하세요.")
        st.caption("주의 1.0m / 6m/s, 보류 검토 1.5m / 8m/s는 제안 코드의 임의 참고 기준이며 공식 안전 기준이 아닙니다.")
    st.link_button("🌦 기상청 날씨누리 확인", "https://www.weather.go.kr/", use_container_width=True)
    with st.expander("💡 원래 코드의 대안 후보 확인"):
        st.write("삼길포항 내항 잔교 / 대부도 탄도항 안쪽 석축")
        st.warning("위 장소는 사용자가 제안한 후보명입니다. 실제 낚시 허용 여부·출입 통제·발판·주차·기상을 확인하지 않았습니다. 악천후의 안전한 대안으로 추천하지 않습니다. 위험하면 출조를 연기하세요.")
    st.markdown("##### 🚢 선상 낚시 예약 사이트")
    st.caption("외부 사이트로 이동합니다. 실제 예약·출항 여부는 해당 업체에서 확인하세요.")
    # 사용자가 제공한 주소에서 누락된 마침표를 복구한 링크입니다.
    st.link_button("🚤 마이피싱", "https://www.myfishing.co.kr", use_container_width=True)
    st.link_button("⚓ 물반고기반", "https://www.moolban.com", use_container_width=True)
    st.link_button("🌊 선상24", "https://www.sunsang24.com", use_container_width=True)

with tab_fresh:
    st.subheader("🎣 민물 포인트 자리 & 주차 체크라용")
    st.caption("원래 코드의 가상 포인트는 예시입니다. 자리·주차 상태는 실시간 정보가 아닙니다.")
    examples = ["당진 ○○ 저수지 (상류 포인트)", "예산 □□ 수로", "아산 △△ 낚시터 (좌대)", "직접 입력"]
    choice = st.selectbox("포인트 선택", examples)
    actual = st.text_input("실제 포인트 이름", key="fresh_actual_" + choice)
    parking = st.text_input("직접 확인한 주차 정보", placeholder="미확인이면 비워 두세요", key="parking_" + choice)
    memo = st.text_area("전화로 확인한 자리 상황·확인 시각", placeholder="예: 11월 3일 09:00 관리실 문의, 방문 전 재확인 필요", height=80, key="memo_" + choice)
    phone = st.text_input("실제 문의 전화번호", placeholder="010-1234-5678", key="phone_" + choice)
    if phone:
        clean = re.sub(r"[\s()\-]", "", phone)
        if re.fullmatch(r"\+?\d{8,15}", clean, flags=re.ASCII):
            st.markdown(f"[📞 문의 전화 걸기 · {clean}](tel:{clean})")
            st.caption("휴대폰의 전화 앱을 엽니다. PC는 전화 연결 앱이 필요할 수 있습니다.")
        else:
            st.warning("전화번호는 숫자 8~15자리로 입력하세요. +, 공백, 괄호, 하이픈을 사용할 수 있습니다.")
    else:
        st.info("전화번호 등록 후 실제 전화 연결 링크가 표시됩니다.")
    st.caption("주차 허용·낚시 가능 여부는 관리 주체에 확인하세요. 입력 메모는 현재 세션에서만 유지됩니다.")

SEA = ["🪪 신분증·선상 예약 정보", "🛟 구명조끼", "🎣 낚싯대·릴·줄", "🧤 장갑·펜치·바늘빼기", "🧊 아이스박스·얼음", "💊 멀미약 (제품 설명서·전문가 안내 준수)", "🕶️ 선글라스·모자·자외선 차단"]
FRESH = ["🎣 낚싯대·받침대", "🪑 의자·파라솔 (강풍 시 사용 중지)", "🐛 미끼·채비", "🔦 헤드랜턴·찌불·여분 배터리", "🦟 기피제 (제품 표시사항 준수)", "☕ 물·음료·간식", "🧻 수건·휴지·쓰레기봉투", "🛟 구명조끼·미끄럼 방지 신발"]

# 탭 전환 때에도 모든 체크 위젯이 렌더링되므로 세션 상태가 유지됩니다.
with tab_checklist:
    st.subheader("📋 출조 전 필수 준비물 점검이라용")
    with st.expander("💾 준비물 백업 · 불러오기"):
        upload = st.file_uploader("이 앱에서 저장한 JSON 파일", type=["json"])
        if st.button("준비물 불러오기", disabled=upload is None):
            try:
                if upload.size > 100000:
                    raise ValueError("파일이 너무 큽니다.")
                payload = json.loads(upload.getvalue().decode("utf-8"))
                if not isinstance(payload, dict) or payload.get("version") != 1:
                    raise ValueError("이 앱의 준비물 백업 파일이 아닙니다.")
                updates = {}
                for group, items in [("sea", SEA), ("fresh", FRESH)]:
                    values = payload.get(group)
                    if not isinstance(values, list) or len(values) != len(items) or any(type(v) is not bool for v in values):
                        raise ValueError("준비물 데이터 형식이 올바르지 않습니다.")
                    updates.update({f"{group}_{i}": value for i, value in enumerate(values)})
                st.session_state.update(updates)
                st.success("불러왔어용!")
            except (ValueError, UnicodeError, TypeError) as exc:
                st.error(f"불러오기 실패: {exc}")
    c_sea, c_fresh = st.columns(2)
    for col, group, label, items in [(c_sea, "sea", "🌊 바다 낚시", SEA), (c_fresh, "fresh", "🎣 민물 낚시", FRESH)]:
        with col:
            st.markdown(f"#### {label}")
            for i, item in enumerate(items):
                st.checkbox(item, key=f"{group}_{i}")
    completed = sum(bool(st.session_state.get(f"{g}_{i}", False)) for g, items in [("sea", SEA), ("fresh", FRESH)] for i in range(len(items)))
    st.progress(completed / (len(SEA) + len(FRESH)), text=f"전체 준비 완료 {completed}/{len(SEA) + len(FRESH)}개")
    payload = {"version": 1, "sea": [bool(st.session_state.get(f"sea_{i}", False)) for i in range(len(SEA))], "fresh": [bool(st.session_state.get(f"fresh_{i}", False)) for i in range(len(FRESH))]}
    st.download_button("💾 준비물 체크 결과 저장", json.dumps(payload, ensure_ascii=False, indent=2), "fishing-checklist.json", "application/json", use_container_width=True)

st.caption("💡 아버지를 위한 맞춤형 낚시 비서 | 항상 안전을 최우선으로 하세용!")
