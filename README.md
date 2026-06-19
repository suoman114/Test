# PKG Dashboard

Bitbucket Server(Data Center)를 패키지 저장소로 사용하는 팀을 위한 **사내 패키지 관리 대시보드**.
사이트별 tar 패키지를 한눈에 보고, 다운로드 / (예정)업로드 / (예정)버전 비교를 할 수 있다.

자세한 설계·결정 사항은 [`CLAUDE.md`](./CLAUDE.md) 참고.

## 구성

- `backend/` — FastAPI. Bitbucket Server REST 1.0 연동, tar 다운로드.
- `frontend/` — Next.js 대시보드. 사이트 목록 / 버전 이력.

## 빠른 시작

### 1) 백엔드

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Bitbucket URL/토큰/프로젝트키 채우기
uvicorn app.main:app --reload --port 8000
```

API 문서: http://localhost:8000/docs

### 2) 프론트엔드

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

대시보드: http://localhost:3000

## Docker 로 배포

nginx 단일 진입점(`:8080`) 뒤에 백엔드/프론트엔드를 둔다. 브라우저는 같은 오리진으로
`/api` 를 호출하므로 호스트별 설정·CORS 가 필요 없다.

```bash
cp backend/.env.example backend/.env   # BITBUCKET_* 채우기 (필수)
docker compose up -d --build
# 접속: http://<호스트>:8080
```

- `proxy`(nginx): `/`, `/api`, `/docs` 라우팅, tar 업로드 위해 `client_max_body_size 1024m`
- `backend`: FastAPI + git(업로드 push 용), 감사 DB 는 `audit-data` 볼륨에 영속화
- `frontend`: Next.js standalone 빌드

> 참고: 서버 컴포넌트(목록 페이지)는 컨테이너 내부에서 `INTERNAL_API_BASE=http://backend:8000`
> 로, 브라우저는 프록시 상대경로로 백엔드를 호출한다 (`lib/api.ts` 가 분기).

## 주요 환경변수 (backend/.env)

| 변수 | 설명 |
|------|------|
| `BITBUCKET_BASE_URL` | Bitbucket Server 주소 |
| `BITBUCKET_PROJECT_KEY` | 패키지 repo 들이 있는 프로젝트 키 |
| `BITBUCKET_TOKEN` | 서비스 계정 Personal Access Token |
| `PACKAGE_TAR_PATH` | repo 내 tar 경로 (기본 `package.tar`) |
| `REPO_SLUG_FILTER` | 노출할 repo slug 정규식 (선택) |

## 현재 상태

- [x] 백엔드: 사이트(repo)/버전(tag) 조회, tar 다운로드
- [x] 프론트: 사이트 목록 + 버전 이력 테이블
- [x] tar 업로드 → 신규 버전(tag) 발행
- [x] 버전 비교 (tar 내부 파일 diff + 커밋 범위)
- [x] 감사 로그 (다운로드/업로드 기록, SQLite)

> 업로드 기능은 런타임에 `git` 바이너리가 필요합니다(Docker 이미지에 포함).
