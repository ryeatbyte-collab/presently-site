# PRESENTLY 사이트 작성 규칙

> 글을 추가하거나 옮길 때 이 문서를 기준으로 작성합니다. 규칙이 바뀌면 이 문서를 먼저 업데이트.

## 1. URL 구조 — 폴더형 (확장자 없음)

```
/posts/{slug}/                  → presently.at/posts/{slug}/
  └── index.html                글 페이지
  └── cover.jpg                 대표 이미지
  └── {기타-이미지}.jpg          본문 이미지
```

- **모든 글 자산(이미지·동영상)은 그 글 폴더 안에** 둘 것 (글마다 자기 폴더)
- 이미 있던 `post-egg.html` 스타일 (단일 파일 + 확장자) 은 **사용하지 않음** — 신규 글은 모두 폴더형

## 2. Slug 규칙

- **소문자 영문 + 하이픈** (`-`)
- 단어 2~4개, 짧을수록 좋음
- **날짜·연도 포함 금지** (에버그린 콘텐츠라 URL이 늙어 보이면 손해)
- 카테고리 prefix 없음 (분류는 페이지 메타로)

| 한글 제목 | Slug |
|---|---|
| 키토제닉 책과 유튜버 추천 | `keto-books` |
| 달걀에 대한 모든 것 | `egg-guide` |
| 올리브오일의 모든 것 | `olive-oil` |
| 화씨 108° 목욕 | `bath-108` |

## 3. 페이지 메타 (글마다 필수)

| 항목 | 형식 / 규칙 | 예시 |
|---|---|---|
| `<title>` | `{핵심 제목 + 후킹} — PRESENTLY` (50~60자) | `키토제닉 입문서 7권 추천 — 한 달 해본 후기 \| PRESENTLY` |
| H1 | 글 자체 제목, 더 풍부하게 (~80자) | `키토제닉 관련해서 읽은 책 7권과 추천 유튜버 — 한 달 직접 해본 기록` |
| meta description | 첫 30자 안에 핵심 키워드, 150~160자 | `글루코스 혁명, 비만 코드, 지방의 진실 등 키토 입문서 7권을 직접 읽고 정리. 추천 유튜버 2명과 한 달 만에 4kg 감량한 식단 기록까지.` |
| `og:title` | `<title>` 과 동일 또는 더 짧게 | |
| `og:description` | meta description 과 동일 | |
| `og:image` | 대표 이미지 절대 URL | `https://presently.at/posts/keto-books/cover.jpg` |
| `og:type` | `article` | |
| `og:url` | 절대 URL (canonical과 동일) | `https://presently.at/posts/keto-books/` |
| `<link rel="canonical">` | 절대 URL | 위와 동일 |
| `<time datetime="YYYY-MM-DD">` | ISO 8601 형식 | `<time datetime="2026-04-23">2026.04.23</time>` |

## 4. 작성자

- 표시 이름: **`nana`**
- HTML: `<span class="author">글 · nana</span>`
- Article schema: `"author": { "@type": "Person", "name": "nana" }`

## 5. 카테고리 분류

| 카테고리 | 한글 | 포함 주제 |
|---|---|---|
| **食 Food** | 먹는 것 | 음식, 식재료, 식단, 영양, 다이어트, 요리, 키토 등 |
| **浴 Bath** | 씻는 것 | 목욕, 온도, 스파, 입욕제, 사우나 |
| **書 Reading** | 읽는 것 | 책 리뷰, 문구, 노트, 만년필 |
| **心 Notes** | 생각하는 것 | 철학, 일상, 짧은 생각, 일기 |

판단 기준: 글의 *주제*가 어디에 속하는지. 이번 키토 책 리뷰처럼 책 형태이지만 주제는 식단이면 **食**.

## 6. 이미지 규칙

### 파일명
- **영문 소문자 + 하이픈** + 설명적
- ✅ `cover.jpg`, `keto-books-glucose-revolution.jpg`, `smartlog-screen.png`
- ❌ `IMG_3842.JPG`, `사진1.jpg`

### 처리
- **포맷**: 사진은 JPG (또는 WebP), 스크린샷·일러스트는 PNG
- **사이즈**: 가로 최대 **1600px** (모바일 + 레티나 대응 충분)
- **품질**: JPG 80~85% 압축
- **목표 용량**: 한 장 1MB 이하 (대표 이미지도 1.5MB 이하)

### alt 텍스트
- **한글로 자세히** 묘사
- ✅ `스마트로그 앱 화면 — 혈당 78, 케톤 1.2 표시`
- ❌ `image1`, `사진`

## 7. AEO/SEO 필수 항목 (글 페이지마다)

### 7-1. Article schema.org (JSON-LD)
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "글 제목",
  "description": "...",
  "image": ["https://presently.at/posts/{slug}/cover.jpg"],
  "datePublished": "2026-04-23",
  "dateModified": "2026-04-23",
  "author": { "@type": "Person", "name": "nana" },
  "publisher": {
    "@type": "Organization",
    "name": "PRESENTLY",
    "logo": { "@type": "ImageObject", "url": "https://presently.at/logo.png" }
  },
  "mainEntityOfPage": "https://presently.at/posts/{slug}/"
}
```

### 7-2. Speakable schema (음성 검색 AEO)
```json
{
  "@type": "WebPage",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".lead", "h1"]
  }
}
```
→ 본문 첫 단락에 `class="lead"` 부여

### 7-3. (해당하면) FAQ schema, HowTo schema
- 레시피 글 → HowTo schema
- "Q&A" 형식 글 → FAQ schema

## 8. 본문 구조

- **H1 1개만** (페이지 최상단, 글 제목)
- **H2** 큰 섹션 (예: "입문서 7권", "추천 유튜버", "한 달 후기")
- **H3** 소제목 (예: 책 한 권씩)
- 첫 단락: **리드 문장** (`<p class="lead">`) — 검색 미리보기/Speakable schema 대상
- 마지막: **관련 글 링크** 2~3개 (내부 링크는 SEO 핵심)

## 9. 사이트맵 / robots / 리디렉트

- `sitemap.xml` — 글 추가할 때마다 업데이트
- `robots.txt` — 사이트맵 URL 명시
- `_redirects` (Cloudflare Pages) — URL 변경 시 301 리디렉트로 SEO 권한 보존

## 10. 발행 후 체크리스트

- [ ] 페이지 작성 (위 메타 / 본문 구조 따름)
- [ ] 이미지 최적화 + 폴더에 저장
- [ ] Article schema JSON-LD 삽입
- [ ] index.html (홈)에 카드 추가/교체
- [ ] sitemap.xml 업데이트
- [ ] (URL 변경된 경우) `_redirects` 한 줄 추가
- [ ] commit + push → Cloudflare Pages 자동 배포
- [ ] 1~2분 후 라이브 확인 (`Cmd+Shift+R`)
- [ ] (주기적으로) Google Search Console / Naver Search Advisor 에 URL 제출
