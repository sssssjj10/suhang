import base64
import io
import json
import uuid
from datetime import date
from urllib.parse import quote, urlparse

try:
    import qrcode
except ImportError:
    qrcode = None
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

st.set_page_config(page_title="오늘 뭐 먹지?", page_icon="🍳", layout="wide")

# 외부 API 키 없이 작동하는 큐레이션 메뉴 데이터입니다.
# 데이터 형식: 이름, 종류, 주재료, 선택 재료, 시간, 조리 단계
RAW = [
 ("김치볶음밥", "한식", "김치,밥", "계란,대파,참기름,햄", 15, ["김치를 잘게 썰고 기름을 두른 팬에서 볶아요.", "밥을 넣고 고루 볶아 간장으로 간해요.", "원한다면 익힌 계란과 참기름을 곁들여요."]),
 ("계란볶음밥", "중식", "계란,밥", "대파,당근,간장", 10, ["팬에 기름을 두르고 대파를 볶아요.", "계란을 넣어 완전히 익도록 저어 볶아요.", "밥을 넣어 볶고 간장과 소금으로 간해요."]),
 ("된장찌개", "한식", "된장,두부", "애호박,양파,감자,대파", 25, ["채소와 두부를 한입 크기로 썰어요.", "물이나 육수에 된장을 풀고 단단한 채소부터 끓여요.", "두부와 나머지 채소를 넣고 익힌 뒤 간을 맞춰요."]),
 ("김치찌개", "한식", "김치,돼지고기", "두부,대파,양파", 30, ["김치와 돼지고기를 냄비에서 볶아요.", "물을 붓고 고기가 속까지 충분히 익도록 끓여요.", "두부와 대파를 넣고 간을 맞춰 더 끓여요."]),
 ("간장계란밥", "한식", "계란,밥,간장", "참기름,김", 5, ["계란을 취향에 맞게 부치되 안전을 위해 충분히 익혀요.", "따뜻한 밥 위에 계란을 올려요.", "간장을 조금씩 넣어 간하고 참기름과 김을 곁들여요."]),
 ("참치마요 덮밥", "한식", "참치,밥,마요네즈", "계란,김,양파", 10, ["참치는 기름을 빼고 마요네즈와 섞어요.", "계란을 사용한다면 완전히 익혀 잘게 부숴요.", "밥 위에 참치와 계란을 올리고 김을 곁들여요."]),
 ("제육볶음", "한식", "돼지고기,고추장", "양파,대파,간장,마늘", 25, ["돼지고기를 고추장, 간장, 다진 마늘로 양념해요.", "팬에서 고기를 볶다가 썬 채소를 넣어요.", "고기가 속까지 충분히 익도록 볶고 간을 맞춰요."]),
 ("비빔국수", "한식", "소면,고추장", "오이,계란,식초,설탕", 15, ["소면을 포장지 안내에 따라 삶고 찬물에 헹궈요.", "고추장에 식초와 설탕을 조금씩 섞어 양념장을 만들어요.", "면을 양념에 비비고 오이나 익힌 계란을 올려요."]),
 ("알리오 올리오", "양식", "파스타면,마늘,올리브오일", "페페론치노,파슬리", 20, ["파스타면을 포장지 안내대로 삶고 면수를 남겨요.", "팬에 올리브오일과 편마늘을 넣고 약불에서 익혀요.", "면과 면수를 조금 넣고 섞은 뒤 소금으로 간해요."]),
 ("토마토 파스타", "양식", "파스타면,토마토소스", "양파,마늘,치즈", 20, ["파스타면을 삶아요.", "팬에 기름을 두르고 양파와 마늘을 볶은 뒤 소스를 넣어요.", "면과 소스를 섞고 취향에 따라 치즈를 올려요."]),
 ("감자전", "한식", "감자", "양파,전분", 20, ["감자를 씻어 껍질을 벗기고 갈아요.", "물기를 살짝 빼고 소금으로 간해요. 필요하면 전분을 더해요.", "기름 두른 팬에 얇게 펴서 앞뒤로 충분히 익혀요."]),
 ("프렌치토스트", "간편식", "식빵,계란,우유", "버터,설탕", 10, ["계란과 우유를 섞어요.", "식빵을 계란물에 적셔요.", "버터나 기름을 두른 팬에서 계란물이 완전히 익도록 양면을 구워요."]),
 ("채소 샌드위치", "간편식", "식빵,양상추,토마토", "치즈,마요네즈,오이", 10, ["채소를 흐르는 물에 씻고 물기를 닦아요.", "빵에 원하는 소스를 얇게 발라요.", "채소와 선택 재료를 올린 후 빵을 덮어요."]),
 ("오야코동", "일식", "닭고기,계란,밥", "양파,간장,설탕", 20, ["팬에 물과 간장, 설탕을 조금 넣고 양파를 끓여요.", "닭고기를 넣어 속까지 충분히 익혀요.", "계란물을 부어 완전히 익힌 뒤 밥 위에 올려요."]),
 ("두부 스테이크", "양식", "두부,계란,전분", "양파,간장", 25, ["두부의 물기를 충분히 짜고 으깨요.", "계란과 전분, 잘게 썬 양파를 넣고 치대 모양을 잡아요.", "기름 두른 팬에서 양면과 속까지 익힌 뒤 소스를 곁들여요."]),
 ("떡볶이", "한식", "떡,고추장", "어묵,대파,설탕,간장", 20, ["떡은 제품 안내에 따라 씻거나 불려요.", "물에 고추장과 설탕, 간장을 풀어 끓여요.", "떡과 선택 재료를 넣고 잘 저으며 속까지 익혀요."]),
 ("채소볶음밥", "간편식", "밥,양파,당근", "애호박,간장,대파", 15, ["채소를 작게 썰어요.", "기름 두른 팬에서 채소를 충분히 볶아요.", "밥을 넣어 고루 볶고 간장이나 소금으로 간해요."]),
 ("오이무침", "한식", "오이,고추장,식초", "양파,설탕,참깨", 10, ["오이를 씻어 얇게 썰어요.", "고추장과 식초, 설탕을 조금씩 섞어 맛을 맞춰요.", "오이와 양파를 양념에 버무리고 바로 먹어요."]),
]
RECIPES = [dict(id=i, name=r[0], category=r[1], required=r[2].split(','), optional=r[3].split(','), minutes=r[4], steps=r[5]) for i,r in enumerate(RAW)]
ALIASES = {"달걀":"계란", "달걀들":"계란", "쌀밥":"밥", "흰밥":"밥", "스파게티면":"파스타면", "파스타":"파스타면", "스팸":"햄", "참치캔":"참치", "돼지 고기":"돼지고기", "닭 고기":"닭고기", "슬라이스치즈":"치즈", "양배추":"양배추"}

def normalize(s):
    s = s.strip().lower()
    return ALIASES.get(s, s.replace(' ', ''))

def tokens(text):
    for sep in ['\n', '，', '/', ';', '、']:
        text = text.replace(sep, ',')
    return {normalize(x) for x in text.split(',') if x.strip()}

# 사진/기록은 브라우저 세션별로 분리됩니다. 다른 사용자에게 자동 공개하지 않습니다.
# Streamlit Community Cloud의 로컬 저장소는 영구 저장소가 아닙니다.
if 'diary' not in st.session_state:
    st.session_state.diary = []
if 'selected_recipe' not in st.session_state:
    st.session_state.selected_recipe = None

st.markdown("""<style>
.stApp {background: #fffaf3;}
.block-container {max-width: 1120px; padding-top: 2rem;}
h1,h2,h3 {color: #263d32;}
[data-testid="stMetric"] {background: #ffffff; border-radius:16px; padding:14px;}
.stButton>button {border-radius:12px;}
</style>""", unsafe_allow_html=True)
st.title("🍳 오늘 뭐 먹지?")
st.caption("냉장고 속 재료로 메뉴를 고르고, 오늘 만든 한 접시를 기록해요.")
with st.sidebar:
    st.header("📱 QR로 접속하기")
    st.caption("배포한 앱의 공개 주소를 입력하세요. QR은 이 앱을 여는 접속 수단입니다.")
    public_url = st.text_input("앱 공개 URL", placeholder="https://your-app.streamlit.app")
    if public_url:
        parsed = urlparse(public_url.strip())
        if parsed.scheme == 'https' and parsed.netloc and not parsed.username and not parsed.password and qrcode is None:
            st.warning("QR 생성 기능에 필요한 패키지가 설치되지 않았습니다. requirements.txt를 app.py와 같은 폴더에 올린 뒤 앱을 재시작해 주세요. 메뉴 추천과 갤러리는 계속 사용할 수 있습니다.")
            st.link_button("앱 주소 열기", public_url.strip())
        elif parsed.scheme == 'https' and parsed.netloc and not parsed.username and not parsed.password:
            img = qrcode.make(public_url.strip()); buf = io.BytesIO(); img.save(buf, format='PNG')
            st.image(buf.getvalue(), caption="휴대폰 카메라로 스캔하세요", width=210)
            st.download_button("QR 이미지 다운로드", buf.getvalue(), "menu_qr.png", "image/png")
        else:
            st.warning("https://로 시작하는 공개 앱 주소를 입력하세요.")
    st.divider()
    st.info("API 키 없이 작동하는 18개 메뉴 기반 추천입니다. 생성형 AI가 아닌 재료 일치도 추천이에요.")
    st.caption("알레르기는 제품 성분과 소스까지 직접 확인하세요. 조리 단계는 간단 안내이며 분량은 레시피 링크에서 확인하세요.")

recommend_tab, recipe_tab, gallery_tab = st.tabs(["🥕 메뉴 추천", "📖 선택한 레시피", "📸 나의 요리 갤러리"])
with recommend_tab:
    st.subheader("오늘은 어떤 음식이 당기나요?")
    a,b = st.columns(2)
    with a:
        categories = st.multiselect("음식 종류 (비우면 전체)", ["한식","중식","양식","일식","간편식"])
        craving = st.text_input("먹고 싶은 음식·메뉴", placeholder="예: 볶음밥, 파스타, 찌개")
        ingredients_text = st.text_area("보유 재료", placeholder="예: 밥, 달걀, 대파\n재료는 쉼표나 줄바꿈으로 구분해 주세요.")
    with b:
        max_time = st.slider("최대 조리 시간 (분)", 5, 60, 30, 5)
        excluded_text = st.text_input("제외할 재료", placeholder="예: 돼지고기, 우유")
        strict = st.checkbox("필수 재료를 모두 가진 메뉴만 보기")
        st.caption("제외 재료가 주재료 또는 선택 재료에 있는 메뉴는 제외해요. 자동 알레르기 안전 판정 기능은 아닙니다.")
    owned, excluded = tokens(ingredients_text), tokens(excluded_text)
    matches=[]
    for r in RECIPES:
        req=set(r['required']); all_ing=req|set(r['optional'])
        if categories and r['category'] not in categories: continue
        if r['minutes'] > max_time or excluded & all_ing: continue
        if strict and not req <= owned: continue
        terms=[normalize(t) for t in craving.replace(',', ' ').split() if t.strip()]
        haystack=normalize(' '.join([r['name'], r['category']] + list(all_ing)))
        if terms and not all(t in haystack for t in terms): continue
        hit=req & owned
        # 주재료 일치율을 우선하고, 선택 재료와 조리시간을 보조로 사용합니다.
        score=100*len(hit)/len(req) if owned else 0
        matches.append((score, len(all_ing & owned), -r['minutes'], r))
    matches.sort(key=lambda x:(-x[0],-x[1],-x[2],x[3]['name']))
    st.caption("입력값을 바꾸면 자동으로 추천이 갱신됩니다. 보유 재료를 입력하면 주재료 일치율 순, 미입력 시 조리시간 순입니다.")
    if not matches:
        st.warning("조건에 맞는 메뉴가 없어요. 음식 종류·조리시간·제외 재료를 조정해 주세요. 등록된 메뉴 범위 안에서만 추천합니다.")
    else:
        st.write(f"**추천 메뉴 {len(matches)}개**")
        cols=st.columns(2)
        for n,(score,_,__,r) in enumerate(matches):
            with cols[n%2]:
                with st.container(border=True):
                    st.subheader(r['name'])
                    st.caption(f"{r['category']} · 약 {r['minutes']}분")
                    if owned:
                        st.progress(score/100, text=f"주재료 일치율 {score:.0f}%")
                        st.write("✅ 보유 주재료: " + (', '.join(x for x in r['required'] if x in owned) or '없음'))
                        st.write("🛒 추가 주재료: " + (', '.join(x for x in r['required'] if x not in owned) or '모두 있어요!'))
                    else:
                        st.write("주재료: " + ', '.join(r['required']))
                    if st.button("이 메뉴 선택", key=f"choose_{r['id']}", use_container_width=True):
                        st.session_state.selected_recipe = r['id']
                        st.success("선택했어요! 위의 ‘선택한 레시피’ 탭을 눌러 주세요.")

with recipe_tab:
    selected=st.session_state.selected_recipe
    if selected is None:
        st.info("메뉴 추천 탭에서 ‘이 메뉴 선택’을 눌러 주세요.")
    else:
        r=RECIPES[selected]
        st.header(r['name'])
        st.caption(f"{r['category']} · 약 {r['minutes']}분 · 시간은 참고용입니다.")
        st.write("**주재료:** " + ', '.join(r['required']))
        st.write("**선택 재료:** " + ', '.join(r['optional']))
        st.caption("식용유·소금·물 등 기본 조미료는 별도로 필요할 수 있습니다.")
        for i,step in enumerate(r['steps'],1): st.write(f"**{i}.** {step}")
        st.subheader("영상·블로그 레시피 찾아보기")
        q=quote(r['name']+' 만들기 레시피')
        c,d=st.columns(2)
        c.link_button("▶ YouTube 레시피 검색", f"https://www.youtube.com/results?search_query={q}", use_container_width=True)
        d.link_button("📝 네이버 블로그 레시피 검색", f"https://search.naver.com/search.naver?where=blog&query={q}", use_container_width=True)
        st.caption("위 링크는 특정 작성자를 검증·추천한 게시물이 아니라 해당 메뉴의 최신 검색 결과입니다. 분량·가열 시간·알레르기 성분을 확인하세요.")

with gallery_tab:
    st.subheader("나의 한 접시 기록")
    st.warning("갤러리는 현재 브라우저 세션에서만 유지됩니다. 새로고침·접속 종료·앱 재시작 시 사라질 수 있어요. 기록 후 반드시 JSON 백업을 다운로드하세요. 다른 사용자에게 자동 공개되지 않습니다.")
    with st.form("new_entry", clear_on_submit=True):
        title=st.text_input("요리 이름", max_chars=80)
        cooked=st.date_input("만든 날짜", value=date.today())
        rating=st.slider("만족도",1,5,4)
        memo=st.text_area("한 줄 후기 / 다음에 바꿀 점", max_chars=1000)
        photo=st.file_uploader("완성 사진 (JPEG / PNG / WEBP, 최대 8MB)", type=['jpg','jpeg','png','webp'])
        submitted=st.form_submit_button("📸 갤러리에 저장", use_container_width=True)
    if submitted:
        if not title.strip(): st.error("요리 이름을 입력해 주세요.")
        elif photo is None: st.error("완성 사진을 올려 주세요.")
        elif photo.size>8*1024*1024: st.error("사진은 8MB 이하로 올려 주세요.")
        elif len(st.session_state.diary)>=60: st.error("세션당 최대 60개입니다. 백업 후 일부 기록을 삭제해 주세요.")
        else:
            try:
                with Image.open(photo) as im:
                    if im.width*im.height>25_000_000: raise ValueError("사진 해상도가 너무 큽니다. 2,500만 화소 이하로 줄여 주세요.")
                    im=ImageOps.exif_transpose(im).convert('RGB')
                    im.thumbnail((1400,1400))
                    data=io.BytesIO();im.save(data,format='JPEG',quality=85)
                st.session_state.diary.append(dict(id=uuid.uuid4().hex,title=title.strip(),date=cooked.isoformat(),rating=rating,memo=memo.strip(),photo=base64.b64encode(data.getvalue()).decode('ascii')))
                st.success("현재 세션에 저장했어요. 아래에서 백업도 받아 주세요!")
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as e:
                st.error(f"사진을 처리할 수 없어요. 정상적인 이미지인지 확인해 주세요. {e}")
    with st.expander("💾 기록 백업 / 복원", expanded=True):
        backup=json.dumps({'version':1,'entries':st.session_state.diary},ensure_ascii=False).encode('utf-8')
        st.download_button("전체 기록 JSON 백업 다운로드",backup,"my_cooking_backup.json","application/json",disabled=not st.session_state.diary)
        st.caption("백업에는 사진과 후기가 포함됩니다. 개인정보가 있을 수 있으니 안전하게 보관하세요.")
        restored=st.file_uploader("이 앱에서 받은 JSON 백업 불러오기 (최대 30MB)",type=['json'],key='restore_file')
        if st.button("백업 기록 추가",disabled=restored is None):
            try:
                if restored.size>30*1024*1024: raise ValueError("30MB 이하만 복원할 수 있어요.")
                obj=json.loads(restored.getvalue())
                if not isinstance(obj,dict) or obj.get('version')!=1 or not isinstance(obj.get('entries'),list): raise ValueError("지원하지 않는 백업 형식입니다.")
                incoming=obj['entries']
                if len(incoming)>60: raise ValueError("최대 60개까지 복원할 수 있어요.")
                validated=[]
                for e in incoming:
                    if not isinstance(e,dict): raise ValueError("기록 형식이 올바르지 않습니다.")
                    if not isinstance(e.get('title'),str) or not e['title'].strip() or len(e['title'])>80: raise ValueError("요리 이름이 올바르지 않습니다.")
                    if not isinstance(e.get('memo'),str) or len(e['memo'])>1000: raise ValueError("후기 형식이 올바르지 않습니다.")
                    if type(e.get('rating')) is not int or not 1<=e['rating']<=5: raise ValueError("만족도가 올바르지 않습니다.")
                    date.fromisoformat(e['date'])
                    raw=base64.b64decode(e['photo'],validate=True)
                    if len(raw)>8*1024*1024: raise ValueError("사진이 너무 큽니다.")
                    with Image.open(io.BytesIO(raw)) as im:
                        if im.width*im.height>25_000_000: raise ValueError("사진 해상도가 너무 큽니다.")
                        im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((1400,1400))
                        buf=io.BytesIO();im.save(buf,format='JPEG',quality=85)
                    entry_id=e.get('id')
                    if not isinstance(entry_id,str) or len(entry_id)!=32 or any(c not in '0123456789abcdef' for c in entry_id): raise ValueError("기록 ID가 올바르지 않습니다.")
                    validated.append(dict(id=entry_id,title=e['title'],date=e['date'],rating=e['rating'],memo=e['memo'],photo=base64.b64encode(buf.getvalue()).decode('ascii')))
                existing={e['id'] for e in st.session_state.diary}
                additions=[]
                for e in validated:
                    if e['id'] not in existing: additions.append(e);existing.add(e['id'])
                if len(st.session_state.diary)+len(additions)>60: raise ValueError("복원 후 기록이 60개를 넘습니다.")
                st.session_state.diary.extend(additions)
                st.rerun()
            except (ValueError,TypeError,KeyError,OSError,Image.DecompressionBombError) as e:
                st.error(f"백업 복원 실패: {e}")
    search=st.text_input("내 기록 검색",placeholder="요리 이름 또는 후기")
    entries=sorted([e for e in st.session_state.diary if search.lower() in (e['title']+' '+e['memo']).lower()],key=lambda e:e['date'],reverse=True)
    if not entries: st.info("아직 표시할 기록이 없어요. 첫 요리 사진을 남겨 보세요!")
    grid=st.columns(2)
    for i,e in enumerate(entries):
        with grid[i%2]:
            with st.container(border=True):
                st.image(base64.b64decode(e['photo']),use_container_width=True)
                st.subheader(e['title'])
                st.caption(e['date']+' · '+'⭐'*e['rating'])
                st.write(e['memo'])
                confirm=st.checkbox("이 기록 삭제 확인",key='confirm_'+e['id'])
                if st.button("삭제",key='delete_'+e['id'],disabled=not confirm):
                    st.session_state.diary=[x for x in st.session_state.diary if x['id']!=e['id']]
                    st.rerun()
