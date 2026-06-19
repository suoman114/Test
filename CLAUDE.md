# PKG Dashboard

Bitbucket Server(Data Center)를 패키지 저장소로 사용하는 팀을 위한 **사내 패키지 관리 대시보드**.
사이트별로 tar로 묶인 패키지를 한눈에 보고, 다운로드/업로드/버전 비교를 할 수 있게 한다.

## 목적 / 컨텍스트

- 패키지는 **사이트마다 별도 Bitbucket repo**로 보관되며, 내용물은 tar로 묶여 있다.
- 팀 내부용. 외부 공개 X.
- Bitbucket은 **Server / Data Center** (REST API 1.0).

## 핵심 결정 (defaults)

이 값들은 합의된 기본값이며 `backend/.env`로 조정 가능하다.

| 항목 | 결정 | 비고 |
|------|------|------|
| 호스팅 | 사내 서버 + Docker | tar이 크고 업로드 시 서버가 git push 프록시 역할을 해야 해서 |
| 사이트 → repo 매핑 | Bitbucket **project key** 단위로 repo 목록 (개인 repo면 `~userID`) | `BITBUCKET_PROJECT_KEY` |
| 패키지 모델 | **repo 1개 = tar 여러 개** (recursive 스캔) | 실데이터 반영 (아래 "모델 변경" 참고) |
| 버전 관리 방식 | **파일별 커밋 이력** (덮어쓰기) | 태그 아님 — 같은 tar 를 덮어쓴 커밋들이 곧 버전 |
| 패키지 인식 | 확장자 매칭 | `PACKAGE_EXTENSIONS` (기본 `.tar,.tar.gz,.tgz`) |
| 인증 | **PAT(Bearer)** 또는 **아이디/비번(Basic)** | `BITBUCKET_TOKEN` 또는 `BITBUCKET_USERNAME`+`BITBUCKET_PASSWORD`. username/password 있으면 Basic 우선. 구버전 Bitbucket(PAT 메뉴 없음) 대응 |
| 대용량 tar | Git LFS 권장 (50MB+) | repo 설정에서 LFS 트래킹 |

## 아키텍처

```
┌─────────────┐     REST 1.0      ┌──────────────────┐
│  Frontend   │ ───────────────▶  │  Backend (FastAPI)│ ──▶ Bitbucket Server
│  Next.js    │ ◀───────────────  │  - bitbucket 클라  │
│  대시보드    │     JSON          │  - 메타 캐시(SQLite)│
└─────────────┘                   └──────────────────┘
```

- **Backend**: Python + FastAPI. Bitbucket Server REST 1.0 호출, tar 업로드 수신 후 git push, 메타데이터 캐싱.
- **Frontend**: Next.js (App Router) + Tailwind. 사이트 카드 그리드 → 버전 테이블 → 비교 뷰.
- **DB**: SQLite. 메타 캐시 + 업로드/감사 로그.

## 기능 로드맵

- [x] 1. 모노레포 스캐폴드 (`backend/` + `frontend/`)
- [x] 2. Bitbucket Server 연동: repo/태그/커밋/파일 조회 API
- [x] 3. 프론트엔드 사이트 목록 + 상세(버전 이력)
- [x] 4. tar 업로드 → Bitbucket 커밋 (신규 버전 등록)
- [x] 5. 버전 비교 (tar 내부 파일 트리 diff, 커밋 메타)
- [x] 6. 감사 로그 (누가 언제 무엇을 받아갔나/올렸나)
- [x] 7. Docker 화 (git 포함 backend 이미지 + frontend + nginx 프록시 + compose)

## 오케스트레이션 개발 메모

기능 4·5·6 은 **병렬 서브에이전트**로 동시 개발했다. 충돌을 막기 위해:
- 각 에이전트는 **새 파일만** 생성, 공유 파일(`main.py`, `requirements.txt`,
  `lib/api.ts`, 기존 페이지)은 손대지 않음.
- 오케스트레이터가 마지막에 라우터 등록 / api 함수 / 링크 / 감사 record 호출을 일괄 배선.
- 신규 백엔드 의존성 0 (git=subprocess, tar=tarfile, audit=sqlite3 — 전부 표준 라이브러리).

### 추가된 모듈

| 파일 | 역할 |
|------|------|
| `backend/app/gitops.py` | tar 를 받아 clone→commit→tag→push (subprocess git, Bearer 토큰) |
| `backend/app/routers/uploads.py` | `POST /api/sites/{slug}/versions` (multipart 업로드) |
| `backend/app/tarinspect.py` | tar 멤버 목록·크기 비교 (added/removed/changed) |
| `backend/app/routers/compare.py` | `GET /api/sites/{slug}/compare` (파일 diff + 커밋 범위) |
| `backend/app/db.py` | SQLite 감사 로그 (`record`, `list_events`), `backend/data/audit.db` |
| `backend/app/routers/audit.py` | `GET /api/audit` |

> 주의: 감사 DB는 `backend/data/` 에 생성되며 `.gitignore` 처리됨.
> upload 의 git push 는 런타임에 `git` 바이너리가 필요(Docker 이미지에 포함할 것).

## 디렉토리

```
backend/    FastAPI 앱
  app/
    main.py          엔트리포인트, 라우터 등록
    config.py        환경변수 설정
    bitbucket.py     Bitbucket Server REST 1.0 클라이언트
    schemas.py       Pydantic 응답 모델
    routers/
      sites.py       사이트(repo) 목록/상세
      versions.py    버전(tag/commit) 조회·다운로드
  requirements.txt
  .env.example
frontend/   Next.js 대시보드
```

## 배포 (Docker)

```
proxy(nginx :8080)
  ├─ /, 정적     → frontend(Next.js :3000, standalone)
  └─ /api,/docs  → backend(FastAPI :8000, +git)
volumes: audit-data → backend:/app/data (감사 SQLite 영속화)
```

- `docker-compose.yml`, `backend/Dockerfile`(git 포함), `frontend/Dockerfile`(multi-stage standalone), `deploy/nginx.conf`.
- **server/browser API 주소 분기**: 목록·상세는 서버 컴포넌트라 컨테이너 내부 `INTERNAL_API_BASE=http://backend:8000` 사용,
  브라우저 client 컴포넌트는 프록시 상대경로(`NEXT_PUBLIC_API_BASE=""`). `frontend/lib/api.ts` 가 `typeof window` 로 분기.
- 업로드용 git 바이너리는 backend 이미지에 포함됨.
- 실행: `cp backend/.env.example backend/.env` 후 `docker compose up -d --build`.

> ⚠️ 이미지 빌드는 이 클라우드 세션에서 검증하지 못함 — Docker Hub unauthenticated pull rate-limit(429) +
> 미러(ECR) egress 차단 때문. 구성은 `docker compose config` 로만 검증. **빌드는 사내/빌드 가능한 환경에서 수행**할 것.
> npm/pip 레지스트리 접근만 되면 표준 빌드로 동작하도록 작성됨.

## 모델 변경 (실데이터 반영, 중요)

사내 실제 Bitbucket(v4.12, 개인 repo `~kigap`)에 붙여보니 초기 가정과 달랐다:

| 초기 가정 | 실제 |
|-----------|------|
| repo 1개 = 패키지 1개 (`package.tar`) | repo 1개 안에 tar.gz **여러 개** (루트 + 하위 폴더) |
| 버전 = git tag | 대부분 태그 없음. **같은 파일 덮어쓰기** → 커밋 이력이 버전 |
| 토큰(PAT) 인증 | v4.12 라 PAT 없음 → **아이디/비번(Basic)** |

→ 조회 로직을 **패키지(파일) 단위**로 재설계:
- `GET /api/sites` — repo 목록 (가벼움)
- `GET /api/sites/{slug}/packages` — repo recursive 스캔, 확장자 매칭 파일 = 패키지
- `GET /api/sites/{slug}/packages/versions?path=` — 그 파일의 커밋 이력 = 버전
- `GET /api/sites/{slug}/packages/download?path=&at=` — 다운로드 (at=커밋이면 그 버전)
- 핵심 모듈: `app/packages.py`(스캔/이력), `app/routers/packages.py`.

> 구(舊) 태그 기반 라우터(`versions`/`compare`/`uploads`)와 프론트 페이지(upload/compare)는
> 아직 남아있으나 새 UI 와 분리됨 — **업로드/비교는 새 모델로 재작성 필요(TODO)**.

## 테스트 / 연동 검증

end-to-end 통합 테스트는 **가짜 Bitbucket Server**(REST 1.0 응답을 흉내내는 ASGI 앱)를
띄우고, 클라이언트 transport 를 거기로 갈아끼워 in-process 로 전 구간을 검증한다.
실제 토큰/네트워크 없이 돌아간다.

```bash
cd backend
pip install -r requirements-dev.txt
pytest                 # tests/test_integration.py
```

- 주입 지점: `app/deps.py` 의 `build_client()` + `_test_transport` 전역, `BitbucketClient(transport=...)`.
- 가짜 서버/픽스처: `tests/fake_bitbucket.py`, `tests/conftest.py`.

**사내망에서 실제 Bitbucket 으로 확인**할 때는 (이 클라우드 세션은 사내망에 못 닿을 수 있음):

```bash
cd backend && cp .env.example .env   # BITBUCKET_* 채우기
python scripts/live_smoke.py            # 읽기 전용: 사이트/태그/커밋/크기
python scripts/live_smoke.py --download  # 최신 tar 다운로드까지
```

### 통합 테스트로 잡은 실버그 (수정 완료)

1. **다운로드 스트리밍 클라이언트 조기 종료** — `StreamingResponse` 본문은 핸들러 반환 *뒤* 에
   흘러나가는데 요청-스코프 의존성이 그 전에 httpx 클라이언트를 닫아 `Cannot send a request,
   as the client has been closed` 발생. → 다운로드는 전용 클라이언트를 만들어 스트리머가
   끝까지 들고 있다가 직접 닫도록 변경 (`build_client` + streamer `finally`).
2. **버전 비교 from-태그 미해석** — `compare.py` 가 태그 이름(`from_version`)을 커밋
   해시(`id`/`displayId`)와 직접 비교 → 절대 매칭 안 돼 항상 fallback. → from 태그를
   `list_tags` 로 커밋 해시로 먼저 해석한 뒤 비교하도록 수정.

> 미검증/주의: `bitbucket.file_size()` 의 `browse?size=true` 방식은 가짜 서버 기준이며,
> 실제 Bitbucket 응답 형태는 라이브 스모크로 한 번 확인 필요(크기가 안 잡히면 None 으로
> graceful 하게 빠지므로 치명적이진 않음).

## 개발 메모

- 작업 브랜치: `claude/trusting-carson-c2ukc7`
- 백엔드 로컬 실행: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
- 프론트 로컬 실행: `cd frontend && npm install && npm run dev`
