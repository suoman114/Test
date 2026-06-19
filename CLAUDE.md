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
- [ ] 4. tar 업로드 → Bitbucket 커밋 (신규 버전 등록)
- [ ] 5. 버전 비교 (tar 내부 파일 트리 diff, 커밋 메타)
- [ ] 6. 감사 로그 (누가 언제 무엇을 받아갔나/올렸나)

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

## 개발 메모

- 작업 브랜치: `claude/trusting-carson-c2ukc7`
- 백엔드 로컬 실행: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
- 프론트 로컬 실행: `cd frontend && npm install && npm run dev`
