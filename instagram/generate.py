#!/usr/bin/env python3
"""
PRESENTLY — 인스타그램 자동 콘텐츠 생성 & 포스팅
be.presently | presently.at

사용법:
  python generate.py                  # 오늘의 콘텐츠 생성 + 이미지 만들기 (포스팅 안 함)
  python generate.py --post           # 생성 + 인스타그램 자동 포스팅
  python generate.py --preview        # 캡션만 터미널에 출력
  python generate.py --topic "달걀"   # 특정 주제로 생성

의존성: pip install anthropic pillow requests python-dotenv
"""

import os
import sys
import json
import time
import random
import argparse
import textwrap
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── 의존성 선택적 로딩 ──────────────────────────────────────────
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("[경고] anthropic 패키지 없음. pip install anthropic")

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("[경고] Pillow 패키지 없음. pip install pillow")

# ── 환경 변수 로드 ────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
IG_ACCESS_TOKEN     = os.getenv("IG_ACCESS_TOKEN", "")
IG_USER_ID          = os.getenv("IG_USER_ID", "")
IMAGE_HOSTING_URL   = os.getenv("IMAGE_HOSTING_URL", "")  # 이미지를 공개 URL로 서빙하는 호스트

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 브랜드 설정 ────────────────────────────────────────────────
BRAND = {
    "name": "PRESENTLY",
    "handle": "@be.presently",
    "url": "presently.at",
    "tagline": "매일 나에게 돌아오는 것들",
    "hashtags": [
        "#PRESENTLY", "#나를돌보는삶", "#108도", "#라이프스타일",
        "#약식동원", "#저탄고지", "#일본문구", "#만년필", "#목욕루틴",
        "#바스솔트", "#호보니치", "#수행", "#마음챙김", "#미니멀라이프",
    ],
}

# ── 콘텐츠 토픽 풀 ─────────────────────────────────────────────
TOPIC_POOL = [
    # 먹는 것
    {"category": "food",       "topic": "달걀 고르는 법 — 난각번호 1번의 의미",         "emoji": "🥚"},
    {"category": "food",       "topic": "저탄고지를 철학으로 — 약식동원의 관점",         "emoji": "🥩"},
    {"category": "food",       "topic": "요리사 출신이 실제로 쓰는 주방 칼",             "emoji": "🔪"},
    {"category": "food",       "topic": "동물복지 달걀이 비싼 이유",                     "emoji": "🐓"},
    {"category": "food",       "topic": "계절마다 달라지는 달걀 맛의 비밀",              "emoji": "☀️"},
    # 씻는 것
    {"category": "bath",       "topic": "화씨 108도 — 번뇌를 녹이는 목욕 온도",         "emoji": "🛁"},
    {"category": "bath",       "topic": "사해소금과 엡솜솔트의 차이",                    "emoji": "🧂"},
    {"category": "bath",       "topic": "목욕을 수행으로 만드는 3가지 방법",              "emoji": "🌿"},
    {"category": "bath",       "topic": "에센셜오일 블렌딩 — 긴장 완화 조합",            "emoji": "🌸"},
    # 쓰는 것
    {"category": "stationery", "topic": "Hobonichi vs Stalogy — 만년필에 어울리는 노트", "emoji": "🖊"},
    {"category": "stationery", "topic": "참회일기 쓰는 법 — 하루를 내려놓는 의식",       "emoji": "📖"},
    {"category": "stationery", "topic": "만년필 첫 구매 가이드 — 일본 3대 브랜드",        "emoji": "✒️"},
    {"category": "stationery", "topic": "손으로 쓰는 것이 명상이 되는 이유",             "emoji": "📝"},
    # 향 · 차
    {"category": "scent",      "topic": "Ippodo Tea — 교토 1717년 차집의 말차",          "emoji": "🍵"},
    {"category": "scent",      "topic": "아침 108배 후 향 피우는 이유",                  "emoji": "🕯"},
    {"category": "scent",      "topic": "Noda Horo — 법랑 용기를 10년 쓰는 이유",        "emoji": "🍳"},
    # 몸
    {"category": "body",       "topic": "괄사 — 동양 의학의 기를 아침에 깨우는 법",      "emoji": "🌿"},
    # 철학
    {"category": "philosophy", "topic": "모든 괴로움은 마음이 일으킨다 — 수행자의 자세", "emoji": "📿"},
    {"category": "philosophy", "topic": "108배를 시작한 이유",                           "emoji": "🙏"},
    {"category": "philosophy", "topic": "AI 시대에 손으로 쓰는 것의 의미",               "emoji": "✍️"},
]

# ── 디자인 팔레트 (PIL용) ────────────────────────────────────────
PALETTE = {
    "bg":      "#F9F7F4",
    "bg_dark": "#1C1C1C",
    "sage":    "#3D5140",
    "accent":  "#8B7355",
    "muted":   "#9E9891",
    "white":   "#FFFFFF",
}

CATEGORY_COLOR = {
    "food":        PALETTE["accent"],
    "bath":        PALETTE["sage"],
    "stationery":  "#5C6E7E",
    "scent":       "#7E6E5C",
    "body":        PALETTE["sage"],
    "philosophy":  PALETTE["bg_dark"],
}


# ════════════════════════════════════════════════
# 1. 캡션 생성 (Claude API)
# ════════════════════════════════════════════════

def generate_caption(topic_info: dict) -> dict:
    """Claude API로 인스타그램 캡션 생성"""
    if not HAS_ANTHROPIC:
        return _fallback_caption(topic_info)
    if not ANTHROPIC_API_KEY:
        print("[경고] ANTHROPIC_API_KEY 없음. 폴백 캡션 사용.")
        return _fallback_caption(topic_info)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system_prompt = """당신은 PRESENTLY 브랜드의 인스타그램 콘텐츠 크리에이터입니다.

브랜드 정보:
- 채널: PRESENTLY (@be.presently) | presently.at
- 제품 브랜드: 108° (바스솔트)
- 철학: "매일 나에게 돌아오는 사람들을 위한 브랜드"
- 핵심 가치: 약식동원(藥食同源), 수행으로서의 일상, 동양 철학과 현대 라이프스타일
- 운영자: 레스토랑 출신 + 뷰티/식품 MD 10년 경험, 108배 수행자, 저탄고지, 만년필 일기

콘텐츠 톤:
- 깊고 조용한 톤. 설교하지 않고, 실제로 살고 있는 사람의 이야기.
- 예쁜 척 하지 않음. 현실적이고 솔직함.
- 전문적 지식(요리, 성분, 철학)을 자연스럽게 녹임.
- 한국어로 작성. 이모지 1-2개만 사용.
- 500자 이내.

저장하고 싶어지는 콘텐츠 조건:
1. 첫 줄이 스크롤을 멈추게 해야 함
2. 실질적인 정보나 관점 변화가 있어야 함
3. 브랜드 색깔이 자연스럽게 녹아 있어야 함

출력 형식 (JSON):
{
  "hook": "첫 줄 (스크롤 멈추는 문장)",
  "body": "본문 (3-5문장)",
  "cta": "마지막 문장 (저장 유도 또는 댓글 유도)",
  "full_caption": "hook + 줄바꿈 + body + 줄바꿈 + cta"
}"""

    user_prompt = f"""다음 주제로 인스타그램 캡션을 작성해주세요:

카테고리: {topic_info['category']}
주제: {topic_info['topic']}
이모지: {topic_info['emoji']}

사람들이 저장하고 싶어하고, 친구에게 공유하고 싶어지는 콘텐츠로 만들어주세요."""

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = message.content[0].text.strip()

        # JSON 파싱 시도
        if text.startswith("{"):
            data = json.loads(text)
        else:
            # 마크다운 코드블록 제거
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            data = json.loads(match.group()) if match else _fallback_caption(topic_info)

        return data

    except Exception as e:
        print(f"[오류] 캡션 생성 실패: {e}")
        return _fallback_caption(topic_info)


def _fallback_caption(topic_info: dict) -> dict:
    """API 없을 때 폴백 캡션"""
    hook = f"{topic_info['emoji']} {topic_info['topic']}"
    body = "매일 나에게 돌아오는 것들. 작은 것들이 쌓여 삶이 됩니다."
    cta  = "저장해두고 천천히 읽어보세요 🤍"
    return {
        "hook": hook,
        "body": body,
        "cta":  cta,
        "full_caption": f"{hook}\n\n{body}\n\n{cta}",
    }


# ════════════════════════════════════════════════
# 2. 이미지 생성 (Pillow)
# ════════════════════════════════════════════════

def create_image(topic_info: dict, caption_data: dict) -> Path:
    """1080×1080 브랜드 이미지 생성"""
    if not HAS_PILLOW:
        print("[경고] Pillow 없음. 이미지 생성 건너뜀.")
        return None

    size   = (1080, 1080)
    cat    = topic_info["category"]
    color  = CATEGORY_COLOR.get(cat, PALETTE["accent"])

    img  = Image.new("RGB", size, PALETTE["bg"])
    draw = ImageDraw.Draw(img)

    # ── 상단 컬러 바 ────────────────────────────────
    draw.rectangle([(0, 0), (1080, 8)], fill=color)

    # ── 브랜드 이름 (상단) ──────────────────────────
    _draw_text(draw, "PRESENTLY", (540, 80), size=32,
               color=PALETTE["bg_dark"], anchor="mm", spacing=12)

    # ── 카테고리 아이콘 (이모지 대신 미니멀 도형) ────
    _draw_category_icon(draw, cat, color, cx=540, cy=280)

    # ── 카테고리 레이블 ────────────────────────────
    cat_labels = {
        "food":        "먹는 것",
        "bath":        "씻는 것  ·  108°",
        "stationery":  "쓰는 것",
        "scent":       "향 · 차 · 주방",
        "body":        "몸을 돌보는 것",
        "philosophy":  "철학 · 북저널",
    }
    cat_label = cat_labels.get(cat, cat)
    _draw_text(draw, cat_label.upper(), (540, 370), size=20,
               color=PALETTE["muted"], anchor="mm", spacing=8)

    # ── 주제 텍스트 ──────────────────────────────────
    topic_text = topic_info["topic"]
    # 긴 주제는 em dash 기준으로 두 줄로 나누기
    if "—" in topic_text and len(topic_text) > 18:
        parts = topic_text.split("—", 1)
        lines = [p.strip() for p in parts]
    else:
        lines = _wrap_text(topic_text, max_chars=20)

    topic_y = 460
    line_h  = 72
    for i, line in enumerate(lines[:3]):
        _draw_text(draw, line, (540, topic_y + i * line_h),
                   size=52, color=PALETTE["bg_dark"], anchor="mm")

    # ── Hook 문장 (캡션 첫 줄) ────────────────────────
    hook = caption_data.get("hook", "")
    # 이모지 제거 후 핵심 문장만 추출
    import re as _re
    hook_clean = _re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ\.,!?·—\-]', '', hook).strip()
    if len(hook_clean) > 32:
        hook_clean = hook_clean[:30] + "..."
    hook_y = topic_y + len(lines[:3]) * line_h + 56
    if hook_clean:
        _draw_text(draw, hook_clean, (540, hook_y), size=26,
                   color=PALETTE["accent"], anchor="mm")

    # ── 하단 구분선 + 정보 ──────────────────────────
    draw.rectangle([(80, 920), (1000, 921)], fill=PALETTE["muted"])
    _draw_text(draw, "@be.presently  ·  presently.at", (540, 962),
               size=22, color=PALETTE["muted"], anchor="mm", spacing=6)
    _draw_text(draw, "108°", (540, 1012), size=20,
               color=PALETTE["accent"], anchor="mm", spacing=8)

    # ── 저장 ────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = OUTPUT_DIR / f"presently_{cat}_{timestamp}.jpg"
    img.save(filename, "JPEG", quality=95, optimize=True)
    print(f"[이미지] 저장됨: {filename}")
    return filename


def _draw_category_icon(draw, cat: str, color: str, cx: int, cy: int):
    """카테고리별 미니멀 아이콘 (이모지 대신 선으로 그린 도형)"""
    r = 52  # 아이콘 반지름
    lw = 3  # 선 두께

    if cat == "food":
        # 포크 + 나이프 암시 → 가운데 원
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], outline=color, width=lw)
        draw.ellipse([(cx-12, cy-12), (cx+12, cy+12)], fill=color)

    elif cat == "bath":
        # 욕조 실루엣 → 반원 + 물결선
        draw.arc([(cx-r, cy-r//2), (cx+r, cy+r)], start=0, end=180, fill=color, width=lw)
        draw.line([(cx-r-8, cy+r//2), (cx+r+8, cy+r//2)], fill=color, width=lw)
        # 물결 (작은 호 3개)
        for i, ox in enumerate([-22, 0, 22]):
            draw.arc([(cx+ox-11, cy-r-18), (cx+ox+11, cy-r+4)],
                     start=200, end=340, fill=color, width=lw)

    elif cat == "stationery":
        # 펜 (세로 선 + 삼각형 팁)
        draw.line([(cx, cy-r), (cx, cy+r-16)], fill=color, width=lw)
        draw.polygon([(cx-8, cy+r-16), (cx+8, cy+r-16), (cx, cy+r)], fill=color)
        draw.line([(cx-22, cy-r+8), (cx+22, cy-r+8)], fill=color, width=lw)

    elif cat == "scent":
        # 촛불 → 원 + 불꽃 선
        draw.ellipse([(cx-10, cy+16), (cx+10, cy+r)], outline=color, width=lw)
        draw.line([(cx-10, cy+16), (cx-10, cy+r)], fill=color, width=lw)
        draw.line([(cx+10, cy+16), (cx+10, cy+r)], fill=color, width=lw)
        draw.arc([(cx-18, cy-r), (cx+18, cy+16)], start=220, end=320, fill=color, width=lw)
        draw.arc([(cx-10, cy-r+10), (cx+10, cy)], start=200, end=340, fill=color, width=lw)
        # 불꽃 심플
        draw.ellipse([(cx-7, cy-r-10), (cx+7, cy-r+10)], fill=color)

    elif cat == "body":
        # 잎사귀 → 타원 + 중앙선
        draw.ellipse([(cx-22, cy-r), (cx+22, cy+r)], outline=color, width=lw)
        draw.line([(cx, cy-r+6), (cx, cy+r-6)], fill=color, width=lw)

    elif cat == "philosophy":
        # 책 → 직사각형 + 선들
        draw.rectangle([(cx-r+8, cy-r+10), (cx+r-8, cy+r-10)], outline=color, width=lw)
        for y_off in [-20, -4, 12]:
            draw.line([(cx-r+22, cy+y_off), (cx+r-22, cy+y_off)], fill=color, width=lw)

    else:
        # 기본: 원
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], outline=color, width=lw)


def _draw_text(draw, text, pos, size=40, color="#1C1C1C",
               anchor="mm", spacing=0):
    """폰트 없이도 쓸 수 있는 텍스트 그리기 (시스템 폰트 시도)"""
    font = _get_font(size)
    draw.text(pos, text, font=font, fill=color, anchor=anchor,
              spacing=spacing)


def _get_font(size: int):
    """시스템에서 사용 가능한 폰트 찾기"""
    from PIL import ImageFont

    candidates = [
        # macOS
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/AppleMyungjo.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        # Linux (apt install fonts-noto-cjk)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # 로컬 폰트 (같은 폴더에 넣어두면 자동 인식)
        str(Path(__file__).parent / "NotoSansCJK-Regular.ttc"),
        str(Path(__file__).parent / "font.ttf"),
        # Windows
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
        # 최후의 수단
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, max_chars: int = 16) -> list:
    """긴 텍스트를 여러 줄로 나누기"""
    words  = text.split()
    lines  = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = f"{current} {w}".strip()
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines[:4]  # 최대 4줄


# ════════════════════════════════════════════════
# 3. 인스타그램 Graph API 포스팅
# ════════════════════════════════════════════════

GRAPH_BASE = "https://graph.facebook.com/v19.0"


def post_to_instagram(image_path: Path, caption: str) -> bool:
    """
    Instagram Graph API로 포스팅.

    전제 조건:
      1. Instagram Business 또는 Creator 계정
      2. Facebook Page에 연결됨
      3. Meta Developer App + Instagram Graph API 활성화
      4. long-lived access token (60일) 또는 system user token

    공개 URL이 필요합니다 — 로컬 파일은 직접 업로드 불가.
    IMAGE_HOSTING_URL 환경변수에 이미지 서버 URL을 설정하세요.
    """
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("[오류] IG_ACCESS_TOKEN / IG_USER_ID 환경변수를 .env에 설정해주세요.")
        return False

    if not IMAGE_HOSTING_URL:
        print("[오류] IMAGE_HOSTING_URL을 설정해주세요.")
        print("       이미지를 업로드할 수 있는 공개 URL이 필요합니다.")
        print("       예: GitHub Pages, AWS S3, Cloudflare R2, Vercel")
        return False

    # 파일명 기반 공개 URL 조립
    image_url = f"{IMAGE_HOSTING_URL.rstrip('/')}/{image_path.name}"

    # Step 1: 미디어 컨테이너 생성
    container_url = f"{GRAPH_BASE}/{IG_USER_ID}/media"
    container_data = {
        "image_url":   image_url,
        "caption":     caption,
        "access_token": IG_ACCESS_TOKEN,
    }
    print(f"[Instagram] 미디어 컨테이너 생성 중...")
    r1 = requests.post(container_url, data=container_data, timeout=30)
    r1_json = r1.json()

    if "error" in r1_json:
        print(f"[오류] 컨테이너 생성 실패: {r1_json['error']['message']}")
        return False

    creation_id = r1_json.get("id")
    print(f"[Instagram] 컨테이너 ID: {creation_id}")

    # Step 2: 상태 대기 (최대 30초)
    for _ in range(10):
        time.sleep(3)
        status_url = f"{GRAPH_BASE}/{creation_id}"
        status_r = requests.get(status_url, params={
            "fields": "status_code",
            "access_token": IG_ACCESS_TOKEN,
        }, timeout=15)
        status = status_r.json().get("status_code", "")
        print(f"  상태: {status}")
        if status == "FINISHED":
            break
        elif status == "ERROR":
            print("[오류] 미디어 처리 실패")
            return False

    # Step 3: 실제 포스팅 (publish)
    publish_url = f"{GRAPH_BASE}/{IG_USER_ID}/media_publish"
    publish_data = {
        "creation_id":  creation_id,
        "access_token": IG_ACCESS_TOKEN,
    }
    print(f"[Instagram] 포스팅 중...")
    r2 = requests.post(publish_url, data=publish_data, timeout=30)
    r2_json = r2.json()

    if "error" in r2_json:
        print(f"[오류] 포스팅 실패: {r2_json['error']['message']}")
        return False

    post_id = r2_json.get("id")
    print(f"✅ 포스팅 완료! Post ID: {post_id}")
    return True


# ════════════════════════════════════════════════
# 4. 캡션 조합
# ════════════════════════════════════════════════

def build_full_caption(caption_data: dict, topic_info: dict) -> str:
    """
    최종 캡션 = 본문 + 해시태그
    인스타그램 알고리즘: 해시태그 5-15개 권장
    """
    body = caption_data.get("full_caption", "")

    # 카테고리별 해시태그 + 공통 태그
    cat_tags = {
        "food":        ["#먹는것 #달걀 #식품 #요리 #저탄고지 #약식동원"],
        "bath":        ["#씻는것 #목욕 #바스솔트 #108도 #온센 #스파"],
        "stationery":  ["#쓰는것 #만년필 #문구 #호보니치 #일본문구 #노트"],
        "scent":       ["#향 #차 #말차 #인센스 #주방 #일본"],
        "body":        ["#몸 #괄사 #셀프케어 #동양의학 #웰니스"],
        "philosophy":  ["#철학 #수행 #마음챙김 #108배 #북저널"],
    }
    cat = topic_info.get("category", "food")
    extra_tags = cat_tags.get(cat, [])

    brand_tags = " ".join(BRAND["hashtags"][:8])
    extra_str  = " ".join(extra_tags)

    return f"{body}\n\n{brand_tags} {extra_str}\n\n{BRAND['url']}"


# ════════════════════════════════════════════════
# 5. 메인
# ════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="PRESENTLY 인스타그램 자동 콘텐츠 생성")
    parser.add_argument("--post",    action="store_true", help="인스타그램에 자동 포스팅")
    parser.add_argument("--preview", action="store_true", help="캡션만 출력 (이미지 생성 없음)")
    parser.add_argument("--topic",   type=str, default="",  help="특정 주제 직접 입력")
    parser.add_argument("--cat",     type=str, default="",  help="카테고리 선택 (food/bath/stationery/...)")
    args = parser.parse_args()

    # 주제 선택
    if args.topic:
        topic_info = {
            "category": args.cat or "food",
            "topic":    args.topic,
            "emoji":    "✨",
        }
    elif args.cat:
        pool = [t for t in TOPIC_POOL if t["category"] == args.cat]
        topic_info = random.choice(pool) if pool else random.choice(TOPIC_POOL)
    else:
        # 날짜를 시드로 → 매일 같은 시간에 실행하면 같은 주제
        seed = int(datetime.now().strftime("%Y%m%d"))
        random.seed(seed)
        topic_info = random.choice(TOPIC_POOL)

    print(f"\n{'='*50}")
    print(f"PRESENTLY 인스타그램 콘텐츠 생성")
    print(f"날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")
    print(f"주제: {topic_info['topic']}")
    print(f"카테고리: {topic_info['category']}")
    print(f"{'='*50}\n")

    # 캡션 생성
    print("[1/3] 캡션 생성 중...")
    caption_data = generate_caption(topic_info)
    full_caption = build_full_caption(caption_data, topic_info)

    print("\n── 생성된 캡션 ──────────────────────────")
    print(full_caption)
    print("─────────────────────────────────────────\n")

    if args.preview:
        print("✅ 미리보기 완료.")
        return

    # 이미지 생성
    print("[2/3] 이미지 생성 중...")
    image_path = create_image(topic_info, caption_data)

    # 콘텐츠 저장 (JSON)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    record_path = OUTPUT_DIR / f"record_{timestamp}.json"
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp":    datetime.now().isoformat(),
            "topic_info":   topic_info,
            "caption_data": caption_data,
            "full_caption": full_caption,
            "image_path":   str(image_path) if image_path else None,
        }, f, ensure_ascii=False, indent=2)
    print(f"[기록] {record_path}")

    # 포스팅
    if args.post:
        if image_path is None:
            print("[오류] 이미지가 없어 포스팅 불가.")
            return
        print("[3/3] 인스타그램 포스팅 중...")
        success = post_to_instagram(image_path, full_caption)
        if not success:
            print("\n[힌트] .env 파일에 아래를 설정해야 포스팅이 됩니다:")
            print("  IG_ACCESS_TOKEN=your_token")
            print("  IG_USER_ID=your_instagram_user_id")
            print("  IMAGE_HOSTING_URL=https://your-image-server.com/images/")
    else:
        print("[3/3] --post 옵션 없음. 이미지와 캡션만 저장됨.")
        print(f"\n포스팅하려면: python generate.py --post")

    print(f"\n✅ 완료! 파일: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
