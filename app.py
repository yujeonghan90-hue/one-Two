import json
from datetime import date

import streamlit as st

st.set_page_config(page_title="병동 온보딩 도우미", page_icon="🩺", layout="wide")

SCHEMA_VERSION = 1
DEFAULT = {
    "ward": "우리 병동 · 예시 자료",
    "materials": [
        {"name": "비멸균 장갑", "category": "보호구", "location": "[예시] 처치 준비실 A장 2번째 칸", "guide": "병동의 감염관리 지침에 따라 적절한 규격을 선택하세요. 손위생과 장갑 교체 기준은 공식 지침을 확인하세요.", "notice": "실제 보관 위치와 재고 요청 절차를 담당자에게 확인하세요."},
        {"name": "체온계", "category": "측정 장비", "location": "[예시] 간호사실 측정 장비 보관함", "guide": "사용 전 제품 모델과 병동 승인 설명서, 세척·소독 지침을 확인하세요. 실제 사용은 담당 교육자의 시범과 감독하에 익히세요.", "notice": "측정 방법·소독 방식은 제품과 병동 지침에 따라 다릅니다."},
        {"name": "이동형 혈압계", "category": "측정 장비", "location": "[예시] 간호사실 옆 장비 구역", "guide": "장비 상태와 승인된 사용 지침을 확인하고, 적절한 커프 선택 및 측정 절차는 교육자에게 배우세요.", "notice": "측정값 해석 및 이상 소견 보고는 병동 지침에 따르세요."},
        {"name": "수액 주입기", "category": "의료기기", "location": "[예시] 장비 보관실 B구역", "guide": "기기별 공식 매뉴얼과 병동 교육을 먼저 확인하세요. 설정·알람 대응은 담당 교육자의 직접 교육과 역량 확인 후 수행하세요.", "notice": "이 앱은 주입 속도 설정, 투약 판단 또는 기기 조작 교육을 대체하지 않습니다."},
    ],
    "checklist": [
        {"id": "orientation", "category": "병동 적응", "task": "병동 주요 공간과 물품 보관 장소 확인", "detail": "교육자와 함께 병동을 둘러보고 실제 위치를 확인합니다."},
        {"id": "contact", "category": "병동 적응", "task": "도움 요청 및 보고 체계 확인", "detail": "담당 교육자, 책임 간호사와 연락하는 절차를 확인합니다."},
        {"id": "hygiene", "category": "안전·감염관리", "task": "손위생 및 보호구 지침 교육", "detail": "병동 공식 지침을 읽고 교육자의 시범과 피드백을 받습니다."},
        {"id": "emergency", "category": "안전·감염관리", "task": "응급상황 호출 절차 및 장비 위치 확인", "detail": "실제 호출 방법과 응급 장비 위치는 병동의 최신 지침으로 확인합니다."},
        {"id": "equipment", "category": "장비 교육", "task": "주요 의료기기 공식 교육 참여", "detail": "독립 수행 전 장비별 교육 및 병동 역량 평가 기준을 확인합니다."},
        {"id": "handover", "category": "업무 흐름", "task": "인수인계 및 전산 교육 참여", "detail": "실제 환자 정보 없이 교육용 자료로 절차를 익힙니다."},
    ],
    "faq": [
        {"question": "물품이 보관 장소에 없으면 어떻게 하나요?", "answer": "표시된 장소는 예시입니다. 실제 병동의 재고 확인·보충 요청 담당자와 절차를 교육자에게 확인하세요."},
        {"question": "처음 사용하는 의료기기를 혼자 사용해도 되나요?", "answer": "이 앱의 안내만으로 사용하지 마세요. 병동의 공식 교육, 담당 교육자의 감독 및 독립 수행 기준을 먼저 확인하세요."},
        {"question": "모르는 점이나 이상 상황은 누구에게 물어보나요?", "answer": "담당 교육자 또는 근무 중 책임 간호사에게 즉시 확인하세요. 응급상황은 앱 검색보다 병동의 응급 호출·보고 절차를 우선하세요."},
        {"question": "체크리스트를 완료하면 독립 수행이 가능한가요?", "answer": "아니요. 체크는 개인 학습 기록입니다. 공식 역량 평가나 교육자 승인, 독립 수행 권한을 의미하지 않습니다."},
    ],
}


def validate_bundle(obj):
    if not isinstance(obj, dict) or obj.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("지원하는 백업 형식이 아닙니다.")
    data = obj.get("content")
    if not isinstance(data, dict) or not isinstance(data.get("ward"), str):
        raise ValueError("병동 이름이 올바르지 않습니다.")
    required = {
        "materials": ("name", "category", "location", "guide", "notice"),
        "checklist": ("id", "category", "task", "detail"),
        "faq": ("question", "answer"),
    }
    for group, keys in required.items():
        rows = data.get(group)
        if not isinstance(rows, list) or len(rows) > 500:
            raise ValueError(f"{group}: 목록 형식 또는 항목 수를 확인하세요 (최대 500개).")
        for row in rows:
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) for k in keys):
                raise ValueError(f"{group}: 필수 항목이 없거나 문자열이 아닙니다.")
            if any(len(row[k]) > 10000 for k in keys):
                raise ValueError("개별 항목은 10,000자 이하여야 합니다.")
        if group == "checklist":
            ids = [row["id"] for row in rows]
            if any(not x.strip() for x in ids) or len(set(ids)) != len(ids):
                raise ValueError("체크리스트 ID는 비어 있지 않은 고유한 값이어야 합니다.")
    progress = obj.get("progress", {})
    if not isinstance(progress, dict):
        raise ValueError("학습 기록 형식이 올바르지 않습니다.")
    for key, row in progress.items():
        if not isinstance(key, str) or not isinstance(row, dict):
            raise ValueError("학습 기록 항목을 확인하세요.")
        if not isinstance(row.get("done", False), bool) or not isinstance(row.get("date", ""), str) or not isinstance(row.get("note", ""), str):
            raise ValueError("학습 기록의 완료 여부, 날짜, 메모를 확인하세요.")
        if len(row.get("note", "")) > 2000:
            raise ValueError("학습 메모는 2,000자 이하여야 합니다.")
    return data, progress


def bundle(include_progress=True):
    return json.dumps({"schema_version": SCHEMA_VERSION, "content": st.session_state.content,
                       "progress": st.session_state.progress if include_progress else {}}, ensure_ascii=False, indent=2)


if "content" not in st.session_state:
    st.session_state.content = json.loads(json.dumps(DEFAULT))
    st.session_state.progress = {}
    st.session_state.revision = 0

st.markdown("""<style>
.stApp {background: #f5f8fb;}
.block-container {padding-top: 2rem; max-width: 1180px;}
h1, h2, h3 {color: #123b4a;}
[data-testid="stMetric"] {background: white; padding: 16px; border-radius: 14px; border: 1px solid #dbe7ec;}
[data-testid="stSidebar"] {background: #eaf3f4;}
div.stButton > button {border-radius: 10px;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🩺 병동 배움터")
    st.caption("신규 간호사의 첫걸음을 함께합니다")
    page = st.radio("메뉴", ["🏠 시작하기", "📦 물품 안내", "✅ 교육 체크리스트", "💬 자주 묻는 질문", "⚙️ 자료 관리·백업"])
    st.divider()
    st.info("데이터는 현재 접속 세션에서만 유지됩니다. 새로 접속하거나 세션이 종료되면 사라질 수 있으니 JSON 백업을 내려받으세요.")
    st.caption("로그인·공유 저장소가 없는 교육용 시제품입니다. 병동 공용 배포 전 접근 통제와 보안 검토가 필요합니다.")

content = st.session_state.content
progress = st.session_state.progress
items = content["checklist"]
completed = sum(bool(progress.get(x["id"], {}).get("done", False)) for x in items)
ratio = completed / len(items) if items else 0
st.title("신규 간호사 교육 도우미")
st.caption(content["ward"])
st.warning("⚠️ 초기 자료는 모두 예시입니다. 실제 병동의 최신 지침으로 검토·교체하세요. 환자 이름·등록번호·진료정보 및 직원 개인정보를 입력하지 마세요. 응급상황은 병동 호출·보고 절차를 우선하세요.")

if page == "🏠 시작하기":
    st.header("오늘의 배움, 한눈에")
    a, b, c = st.columns(3)
    a.metric("등록 물품", f"{len(content['materials'])}개")
    b.metric("교육 진행", f"{completed} / {len(items)}")
    c.metric("자주 묻는 질문", f"{len(content['faq'])}개")
    st.subheader("나의 교육 진행률")
    st.progress(ratio, text=f"{ratio:.0%} 완료 · 개인 학습 기록")
    st.markdown("### 이렇게 사용하세요\n1. **물품 안내**에서 이름이나 위치로 검색하세요.\n2. 실제 교육을 받은 뒤 **교육 체크리스트**에 기록하세요.\n3. 반복되는 질문은 **자주 묻는 질문**에서 찾아보세요.\n4. 종료 전 **자료 관리·백업**에서 학습 기록을 내려받으세요.")
    remaining = [x for x in items if not progress.get(x["id"], {}).get("done", False)]
    st.subheader("다음에 확인할 교육")
    if remaining:
        for x in remaining[:3]:
            st.write(f"• {x['task']}")
    else:
        st.success("등록된 학습 항목을 모두 체크했습니다. 공식 역량 평가는 교육자에게 별도로 확인하세요.")

elif page == "📦 물품 안내":
    st.header("어디에 있고, 무엇을 확인하나요?")
    q = st.text_input("물품 이름·위치·설명 검색", placeholder="예: 장갑, 보관실").strip().casefold()
    category = st.selectbox("분류", ["전체"] + sorted({x["category"] for x in content["materials"]}))
    found = [x for x in content["materials"] if (category == "전체" or x["category"] == category) and (not q or q in " ".join(x.values()).casefold())]
    st.caption(f"검색 결과 {len(found)}개")
    for x in found:
        with st.container(border=True):
            st.subheader(x["name"])
            st.caption(x["category"])
            st.write("📍 위치: " + x["location"])
            st.write("📖 기본 안내: " + x["guide"])
            st.info(x["notice"])
    if not found:
        st.info("검색 결과가 없습니다. 다른 단어로 검색하거나 교육자에게 확인하세요.")

elif page == "✅ 교육 체크리스트":
    st.header("나의 교육 체크리스트")
    st.caption("체크는 자가 학습 기록이며 공식 교육 이수 확인이나 독립 수행 승인이 아닙니다.")
    st.progress(ratio, text=f"전체 {len(items)}개 중 {completed}개 완료")
    category = st.selectbox("교육 분류", ["전체"] + sorted({x["category"] for x in items}))
    for item in items:
        if category != "전체" and item["category"] != category:
            continue
        ident = item["id"]
        old = progress.get(ident, {"done": False, "date": "", "note": ""})
        prefix = f"{st.session_state.revision}_{ident}"
        with st.container(border=True):
            st.caption(item["category"])
            done = st.checkbox(item["task"], value=old.get("done", False), key="check_" + prefix)
            st.write(item["detail"])
            note = st.text_area("학습 메모 (개인정보 입력 금지)", value=old.get("note", ""), key="note_" + prefix, max_chars=2000, height=80)
            stamp = old.get("date", "")
            if done and not old.get("done", False):
                stamp = date.today().isoformat()
            if not done:
                stamp = ""
            progress[ident] = {"done": done, "date": stamp, "note": note}
            if stamp:
                st.caption("완료 체크 날짜 (서버 기준): " + stamp)
            if done != old.get("done", False):
                st.rerun()
    if not items:
        st.info("등록된 교육 항목이 없습니다.")

elif page == "💬 자주 묻는 질문":
    st.header("반복 질문, 여기서 먼저 확인하세요")
    q = st.text_input("질문·답변 검색", placeholder="예: 물품, 의료기기, 보고").strip().casefold()
    found = [x for x in content["faq"] if not q or q in (x["question"] + " " + x["answer"]).casefold()]
    st.caption(f"검색 결과 {len(found)}개")
    for x in found:
        with st.expander(x["question"]):
            st.write(x["answer"])
    if not found:
        st.info("등록된 답변이 없습니다. 교육자에게 확인하고 검토된 답변을 자료에 추가하세요.")

else:
    st.header("자료 관리·백업")
    st.info("자료 수정은 현재 세션에만 반영되며 다른 사용자에게 공유되지 않습니다. 공용 기본 자료를 바꾸려면 GitHub의 app.py 안 DEFAULT를 수정한 뒤 배포하세요. 이 화면은 관리자 인증 기능이 아닙니다.")
    st.subheader("1. 백업 내려받기")
    a, b = st.columns(2)
    a.download_button("내 학습 기록 포함 백업", bundle(), "ward_learning_backup.json", "application/json", use_container_width=True)
    b.download_button("교육 자료만 내보내기", bundle(False), "ward_content.json", "application/json", use_container_width=True)
    st.caption("공유할 때는 교육 자료만 내보내기를 이용하세요. 개인 학습 메모를 공용 저장소에 올리지 마세요.")
    st.subheader("2. 백업 불러오기")
    uploaded = st.file_uploader("이 앱에서 내보낸 JSON 파일", type=["json"])
    if st.button("백업 적용 (현재 자료·학습 기록 교체)", disabled=uploaded is None):
        try:
            if uploaded.size > 2_000_000:
                raise ValueError("백업 파일은 2MB 이하여야 합니다.")
            data, saved_progress = validate_bundle(json.loads(uploaded.getvalue().decode("utf-8-sig")))
            st.session_state.content = data
            st.session_state.progress = saved_progress
            st.session_state.revision += 1
            st.rerun()
        except (ValueError, UnicodeError, TypeError, KeyError) as exc:
            st.error(f"백업을 불러오지 못했습니다: {exc}")
    st.subheader("3. 교육 자료 수정")
    st.caption("체크리스트 ID는 기록을 연결하는 고유값입니다. 기존 ID를 바꾸면 해당 항목의 학습 기록 연결이 끊깁니다. 아래 저장 버튼을 눌러야 반영됩니다.")
    with st.form("edit_content"):
        ward = st.text_input("병동 표시 이름", value=content["ward"], max_chars=120)
        st.markdown("**물품 안내** · 아래 표의 셀을 눌러 수정하고 마지막 행에서 추가하세요.")
        materials = st.data_editor(content["materials"], num_rows="dynamic", use_container_width=True, key=f"materials_{st.session_state.revision}", column_order=["name", "category", "location", "guide", "notice"])
        st.caption("name: 물품명 / category: 분류 / location: 위치 / guide: 기본 안내 / notice: 주의사항")
        st.markdown("**교육 체크리스트**")
        checklist = st.data_editor(content["checklist"], num_rows="dynamic", use_container_width=True, key=f"tasks_{st.session_state.revision}", column_order=["id", "category", "task", "detail"])
        st.caption("id: 고유 ID / category: 분류 / task: 교육 항목 / detail: 상세 안내")
        st.markdown("**자주 묻는 질문**")
        faq = st.data_editor(content["faq"], num_rows="dynamic", use_container_width=True, key=f"faq_{st.session_state.revision}", column_order=["question", "answer"])
        st.caption("question: 질문 / answer: 검토된 답변")
        approved = st.checkbox("환자·직원 개인정보가 없으며, 실제 사용 전 교육 담당자의 검토가 필요함을 확인했습니다.")
        save = st.form_submit_button("현재 세션에 자료 저장", type="primary")
    if save:
        if not approved:
            st.error("개인정보 및 검토 안내 확인란을 체크하세요.")
        else:
            try:
                candidate = {"ward": ward, "materials": materials, "checklist": checklist, "faq": faq}
                cleaned, kept = validate_bundle({"schema_version": SCHEMA_VERSION, "content": candidate, "progress": progress})
                st.session_state.content = cleaned
                st.session_state.progress = {x["id"]: kept[x["id"]] for x in checklist if x["id"] in kept}
                st.session_state.revision += 1
                st.rerun()
            except (ValueError, TypeError, KeyError) as exc:
                st.error(f"저장하지 못했습니다: {exc}. 비어 있는 셀은 빈 문자열이라도 입력하세요.")

st.divider()
st.caption("병동 배움터 · 교육 보조용 시제품 | 임상 판단·공식 매뉴얼·역량 평가를 대체하지 않습니다.")
