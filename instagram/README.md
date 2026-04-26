# PRESENTLY 인스타그램 자동화 시스템

매일 블로그 콘텐츠를 기반으로 인스타그램 포스팅을 자동 생성하는 시스템.

---

## 작동 방식

```
블로그 콘텐츠 풀
     ↓
Claude API (claude-opus-4-6)
     → 저장하고 싶어지는 캡션 생성
     ↓
Pillow
     → 1080×1080 브랜드 이미지 생성
     ↓
이미지 → 공개 URL로 업로드 (수동 or 자동)
     ↓
Instagram Graph API
     → @be.presently 자동 포스팅
```

---

## 설치

```bash
cd instagram/
pip install -r requirements.txt
cp .env.example .env
# .env 파일 편집 (API 키 입력)
```

---

## 사용법

```bash
# 캡션만 미리보기 (API 키 없어도 됨)
python generate.py --preview

# 이미지 + 캡션 생성 (포스팅 없음)
python generate.py

# 특정 카테고리로 생성
python generate.py --cat bath

# 직접 주제 입력
python generate.py --topic "사해소금이 일반 소금과 다른 이유" --cat bath

# 생성 + 인스타그램 포스팅
python generate.py --post
```

### 매일 자동 실행 (cron)
```bash
# crontab -e
# 매일 오전 7시 실행
0 7 * * * cd /path/to/presently-site/instagram && python generate.py --post >> logs/daily.log 2>&1
```

---

## Instagram API 설정 가이드

### Step 1. Meta Developer App 만들기

1. [Meta for Developers](https://developers.facebook.com) 접속
2. **My Apps → Create App** 클릭
3. App Type: **Business** 선택
4. App 이름: `PRESENTLY` (임의)
5. **Add Product → Instagram Graph API** 추가

### Step 2. Instagram Business 계정 연결

1. Instagram 계정을 **Professional Account** (Business 또는 Creator)로 전환
   - 인스타그램 앱 → 설정 → 계정 → 직업 계정으로 전환
2. Facebook Page 만들기 (없으면)
3. Instagram Business 계정을 Facebook Page에 연결
   - Facebook Page → 설정 → Instagram → 연결

### Step 3. 권한 설정

Facebook Developer Console에서:
- **instagram_basic**
- **instagram_content_publish**
- **pages_read_engagement**

권한을 앱에 추가.

### Step 4. Access Token 발급

**방법 A: Graph API Explorer 사용 (테스트용, 60일)**
1. [Graph API Explorer](https://developers.facebook.com/tools/explorer/) 접속
2. App 선택 → `instagram_basic`, `instagram_content_publish` 체크
3. **Generate Access Token** → Facebook 로그인
4. 발급된 token을 장기 token으로 교환:

```bash
curl "https://graph.facebook.com/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id=YOUR_APP_ID
  &client_secret=YOUR_APP_SECRET
  &fb_exchange_token=SHORT_LIVED_TOKEN"
```

**방법 B: System User Token (무기한, 운영용 권장)**
1. Meta Business Suite → Business Settings → Users → System Users
2. System User 생성 → Admin 권한
3. **Generate New Token** → 위 권한 추가
4. 만료 없는 토큰 발급

### Step 5. Instagram User ID 확인

```bash
curl "https://graph.facebook.com/me/accounts?access_token=YOUR_TOKEN"
# → 페이지 목록. 각 페이지 id 확인

curl "https://graph.facebook.com/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
# → instagram_business_account.id 가 IG_USER_ID
```

### Step 6. .env 파일 완성

```
ANTHROPIC_API_KEY=sk-ant-...
IG_USER_ID=17841400000000000
IG_ACCESS_TOKEN=EAAxxxxxx...
IMAGE_HOSTING_URL=https://your-image-host.com/
```

---

## 이미지 호스팅 옵션

Instagram API는 **공개 URL의 이미지**만 허용. 로컬 파일 직접 업로드 불가.

| 옵션 | 비용 | 난이도 | 추천도 |
|------|------|--------|--------|
| **GitHub Pages** | 무료 | 쉬움 | ⭐⭐⭐ |
| **Cloudflare R2** | 무료 10GB/월 | 보통 | ⭐⭐⭐⭐ |
| **AWS S3** | $0.023/GB | 보통 | ⭐⭐⭐ |
| **Vercel** | 무료 (100GB/월) | 쉬움 | ⭐⭐⭐⭐ |

**가장 쉬운 방법 — GitHub Pages:**
```bash
# presently-images 라는 GitHub 레포 만들기
# 생성된 이미지를 거기에 push
# https://yourusername.github.io/presently-images/파일명.jpg 으로 접근
```

**스크립트에서 GitHub 자동 push 추가 예시:**
```python
import subprocess
def upload_to_github(image_path):
    repo = "/path/to/presently-images"
    import shutil
    shutil.copy(image_path, repo)
    subprocess.run(["git", "-C", repo, "add", "."])
    subprocess.run(["git", "-C", repo, "commit", "-m", "add image"])
    subprocess.run(["git", "-C", repo, "push"])
```

---

## 생성되는 파일

```
instagram/
├── generate.py         # 메인 스크립트
├── requirements.txt
├── .env.example
├── README.md
└── output/             # 자동 생성
    ├── presently_food_20260426_070000.jpg   # 이미지
    └── record_20260426_070000.json          # 캡션 + 메타데이터 기록
```

---

## 트러블슈팅

**"The image url is invalid"**
→ IMAGE_HOSTING_URL이 실제로 공개 접근 가능한지 확인.
→ HTTPS여야 함 (HTTP 불가).

**"Application does not have permission"**
→ instagram_content_publish 권한 확인.
→ Instagram 계정이 Business/Creator 계정인지 확인.

**"Media ID is not published"**
→ Step 2 (컨테이너 생성 후 상태 대기)의 시간을 늘려보세요.
→ 이미지 크기가 너무 크면 처리 시간이 걸림 (1080×1080, JPEG 권장).

**캡션이 이상함**
→ ANTHROPIC_API_KEY 확인.
→ --preview 옵션으로 먼저 테스트.
