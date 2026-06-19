"""가짜 Bitbucket Server 를 상대로 한 end-to-end 통합 테스트.

클라이언트 → 라우터 → 응답 파싱 → tar 다운로드/비교 → 감사 로그까지
한 번에 검증한다.
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

    # site-a 는 최신 태그/크기/갱신일이 채워져야 한다.
    a = sites["site-a"]
    assert a["name"] == "Site A"
    assert a["latest_version"] == "v1.1.0"
    assert a["size_bytes"] and a["size_bytes"] > 0
    assert a["updated_at"] is not None

    # site-b 는 태그가 없으므로 latest_version 이 None.
    assert sites["site-b"]["latest_version"] is None


def test_get_site(client):
    r = client.get("/api/sites/site-a")
    assert r.status_code == 200
    body = r.json()
    assert body["slug"] == "site-a"
    assert body["latest_version"] == "v1.1.0"


def test_list_versions(client):
    r = client.get("/api/sites/site-a/versions")
    assert r.status_code == 200
    versions = r.json()
    names = [v["name"] for v in versions]
    assert names == ["v1.1.0", "v1.0.0"]
    # 커밋 메타가 채워져야 한다.
    top = versions[0]
    assert top["author"] == "alice"
    assert top["message"] == "Publish v1.1.0"
    assert top["size_bytes"] and top["size_bytes"] > 0


def test_download_tar_and_audit(client):
    r = client.get("/api/sites/site-a/versions/v1.0.0/download")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/x-tar")
    assert "site-a-v1.0.0.tar" in r.headers["content-disposition"]
    # 실제 tar 바이트인지 확인.
    import io
    import tarfile

    with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:*") as tf:
        assert "app.py" in tf.getnames()

    # 다운로드가 감사 로그에 기록됐는지 확인.
    audit = client.get("/api/audit").json()
    assert any(
        e["action"] == "download"
        and e["slug"] == "site-a"
        and e["version"] == "v1.0.0"
        for e in audit
    )


def test_compare_versions(client):
    r = client.get(
        "/api/sites/site-a/compare",
        params={"from_version": "v1.0.0", "to_version": "v1.1.0"},
    )
    assert r.status_code == 200
    body = r.json()

    added = {m["name"] for m in body["added"]}
    removed = {m["name"] for m in body["removed"]}
    changed = {m["name"] for m in body["changed"]}

    assert added == {"README.md"}
    assert removed == {"config.ini"}
    assert changed == {"app.py"}

    # from(v1.0.0=c1) 을 올바로 해석했다면 fallback note 없이
    # 그 사이 커밋(c2) 만 남아야 한다.
    assert body["note"] is None
    assert [c["id"] for c in body["commits"]] == ["c2" * 20]
