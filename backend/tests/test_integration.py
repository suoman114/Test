"""가짜 Bitbucket Server 상대 end-to-end 통합 테스트 (패키지 모델).

사이트(repo) → 패키지(tar 파일들, recursive) → 파일별 버전(커밋) → 다운로드 → 감사로그.
"""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_sites(client):
    r = client.get("/api/sites")
    assert r.status_code == 200
    sites = {s["slug"]: s for s in r.json()}
    assert set(sites) == {"site-a", "site-b"}
    assert sites["site-a"]["name"] == "Site A"


def test_list_packages_recursive(client):
    r = client.get("/api/sites/site-a/packages")
    assert r.status_code == 200
    pkgs = {p["path"]: p for p in r.json()}

    # 루트의 tar.gz 와 하위 폴더의 tgz 둘 다 잡혀야 한다. README.md 는 제외.
    assert set(pkgs) == {"ansible.tar.gz", "sub/bash_vcs.tgz"}

    a = pkgs["ansible.tar.gz"]
    assert a["name"] == "ansible.tar.gz"
    assert a["size_bytes"] == 100
    assert a["last_author"] == "alice"          # 최신 커밋(c2)
    assert a["updated_at"] is not None

    nested = pkgs["sub/bash_vcs.tgz"]
    assert nested["size_bytes"] == 50
    assert nested["last_author"] == "carol"


def test_package_versions(client):
    r = client.get(
        "/api/sites/site-a/packages/versions",
        params={"path": "ansible.tar.gz"},
    )
    assert r.status_code == 200
    versions = r.json()
    # ansible.tar.gz 는 커밋 2개 = 버전 2개 (최신순)
    assert [v["author"] for v in versions] == ["alice", "bob"]
    assert versions[0]["message"] == "update ansible"


def test_download_and_audit(client):
    r = client.get(
        "/api/sites/site-a/packages/download",
        params={"path": "sub/bash_vcs.tgz"},
    )
    assert r.status_code == 200
    assert r.content == b"BASHVCS"
    assert 'filename="bash_vcs.tgz"' in r.headers["content-disposition"]

    audit = client.get("/api/audit").json()
    assert any(
        e["action"] == "download" and e["slug"] == "site-a"
        and e["detail"] == "sub/bash_vcs.tgz"
        for e in audit
    )
