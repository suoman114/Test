"""tar 내부 멤버 조회 및 diff 헬퍼.

표준 라이브러리(tarfile, io)만 사용한다. tar 바이트는 BitbucketClient.raw_stream
으로 받아서 메모리에 모은 뒤 멤버 목록을 추출한다.
"""
from __future__ import annotations

import io
import tarfile

from .bitbucket import BitbucketClient
from .config import Settings


async def _download_tar_bytes(
    bb: BitbucketClient, slug: str, path: str, ref: str
) -> bytes:
    """특정 ref(tag/commit)의 tar 파일 바이트를 통째로 받아온다."""
    buf = io.BytesIO()
    async with await bb.raw_stream(slug, path, at=ref) as resp:
        resp.raise_for_status()
        async for chunk in resp.aiter_bytes():
            buf.write(chunk)
    return buf.getvalue()


def _members_from_bytes(data: bytes) -> dict[str, int]:
    """tar 바이트에서 {멤버 이름: 크기} 딕셔너리를 만든다 (일반 파일만)."""
    members: dict[str, int] = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
        for m in tf.getmembers():
            if m.isfile():
                members[m.name] = m.size
    return members


async def list_members(
    bb: BitbucketClient, slug: str, ref: str, settings: Settings
) -> dict[str, int]:
    """주어진 ref 의 tar 내부 멤버를 {이름: 크기} 로 반환한다."""
    data = await _download_tar_bytes(bb, slug, settings.package_tar_path, ref)
    return _members_from_bytes(data)


def diff_members(
    a: dict[str, int], b: dict[str, int]
) -> tuple[list[dict], list[dict], list[dict]]:
    """a(=from) 와 b(=to) 멤버를 비교.

    - added:   b 에만 있는 멤버
    - removed: a 에만 있는 멤버
    - changed: 둘 다 있지만 크기가 다른 멤버
    각 항목은 name / from_size / to_size 를 담는다.
    """
    added: list[dict] = []
    removed: list[dict] = []
    changed: list[dict] = []

    for name, size in b.items():
        if name not in a:
            added.append({"name": name, "from_size": None, "to_size": size})

    for name, size in a.items():
        if name not in b:
            removed.append({"name": name, "from_size": size, "to_size": None})

    for name, size_b in b.items():
        if name in a and a[name] != size_b:
            changed.append(
                {"name": name, "from_size": a[name], "to_size": size_b}
            )

    added.sort(key=lambda x: x["name"])
    removed.sort(key=lambda x: x["name"])
    changed.sort(key=lambda x: x["name"])
    return added, removed, changed


__all__ = ["list_members", "diff_members"]
