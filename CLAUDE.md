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
| 사이트 → repo 매핑 | Bitbucket **project key** 단위로 repo 목록을 끌어옴 | `BITBUCKET_PROJECT_KEY` |
| 버전 관리 방식 | **git tag 기반** + tar 파일명 고정 | 파일명에 버전을 박지 않고 tag로 버전을 식별 → 비교/이력이 쉬움 |
| tar 경로 | repo 루트의 고정 경로 | `PACKAGE_TAR_PATH` (기본 `package.tar`) |
| 인증 | 서비스 계정 **Personal Access Token** 1개 | `BITBUCKET_TOKEN`. 추후 사용자별 PAT로 확장 가능 |
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
