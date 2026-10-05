#!/usr/bin/env python3
"""Install an authenticated Dever release; no application configuration is read."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request

RELEASES = "https://github.com/shemic/dever-main/releases"
MAX_METADATA = 2 * 1024 * 1024
MAX_RELEASE = 2 * 1024 * 1024 * 1024
ASSET_HOSTS = {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, stream, code, message, headers, address):
        target = urllib.parse.urlsplit(address)
        if (target.scheme != "https" or target.hostname not in ASSET_HOSTS
                or target.username or target.password or target.port not in (None, 443)
                or target.fragment):
            raise ValueError("发行下载重定向离开官方 HTTPS 站点")
        return super().redirect_request(request, stream, code, message, headers, address)


def download(address):
    # Installation does not inherit HTTP proxy/environment configuration.
    client = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), OfficialRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )
    try:
        return client.open(address, timeout=60)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ValueError("该版本/平台尚无官方发行包，未修改已安装的 Dever") from error
        raise ValueError(f"官方发行下载失败：HTTP {error.code}") from error


def platform_name():
    host = os.uname()
    names = {"x86_64": "linux-x86_64", "aarch64": "linux-aarch64"}
    if host.sysname != "Linux" or host.machine not in names:
        raise ValueError("安装器当前只支持 Linux x86_64/aarch64，且需对应平台已发布工具包")
    return names[host.machine]


def read_bounded(path, limit):
    with path.open("rb") as stream:
        contents = stream.read(limit + 1)
    if len(contents) > limit:
        raise ValueError("发行元数据超过大小限制")
    return contents


def metadata(release, source, selection, platform):
    for filename in ("manifest.json", "manifest.sig"):
        if source:
            contents = read_bounded(source / filename, MAX_METADATA)
        else:
            with download(f"{RELEASES}/{selection}/dever-{platform}.{filename}") as stream:
                contents = stream.read(MAX_METADATA + 1)
            if len(contents) > MAX_METADATA:
                raise ValueError("发行元数据超过大小限制")
        (release / filename).write_bytes(contents)


def authenticate(release, key_path, scratch, platform, requested):
    key = bytes.fromhex(read_bounded(key_path, 256).decode().strip())
    signature = bytes.fromhex(read_bounded(release / "manifest.sig", 256).decode().strip())
    if len(key) != 32 or len(signature) != 64:
        raise ValueError("发行公钥或签名长度错误")
    public_der = scratch / "public.der"
    public_der.write_bytes(bytes.fromhex("302a300506032b6570032100") + key)
    signature_file = scratch / "signature.bin"
    signature_file.write_bytes(signature)
    verified = subprocess.run(
        ["/usr/bin/openssl", "pkeyutl", "-verify", "-pubin", "-keyform", "DER",
         "-inkey", str(public_der), "-rawin", "-in", str(release / "manifest.json"),
         "-sigfile", str(signature_file)],
        env={}, capture_output=True, timeout=15, check=False,
    )
    if verified.returncode:
        raise ValueError("发行签名校验失败，未执行安装程序")
    manifest = json.loads((release / "manifest.json").read_text())
    if (set(manifest) != {"format", "version", "platform", "artifacts", "extensions"}
            or manifest.get("format") != "dever-release-v2" or manifest.get("platform") != platform
            or not isinstance(manifest["extensions"], list) or len(manifest["extensions"]) > 12):
        raise ValueError("发行格式或平台不匹配")
    version = manifest.get("version", "")
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
        raise ValueError("发行版本不是准确的 major.minor.patch")
    if requested != "latest" and version != requested:
        raise ValueError("发行版本与请求不匹配")
    artifacts = manifest.get("artifacts", [])
    if not 1 <= len(artifacts) <= 4096:
        raise ValueError("发行文件数超限")
    catalog = {}
    total = 0
    for artifact in artifacts:
        name, size, digest = artifact["path"], artifact["bytes"], artifact["sha256"]
        if (set(artifact) != {"path", "bytes", "sha256"}
                or not name or name.startswith("/")
                or any(part in ("", ".", "..") for part in name.split("/"))
                or any(character in name for character in ("\\", ":", "\0"))
                or str(PurePosixPath(name)) != name
                or name in catalog or name in ("manifest.json", "manifest.sig")):
            raise ValueError("发行包含不安全或重复路径")
        if type(size) is not int or size < 0 or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("发行文件长度或摘要错误")
        total += size
        if total > MAX_RELEASE:
            raise ValueError("发行解压长度超过 2 GiB")
        catalog[name] = artifact
    if not {"dever-core", "bootstrap/dever", "skills/dever-language/SKILL.md"} <= catalog.keys():
        raise ValueError("首装包缺少核心、bootstrap 启动器或配套 skill")
    return version, catalog, key


def copy_artifact(stream, destination, artifact):
    destination.parent.mkdir(parents=True, exist_ok=True)
    remaining = artifact["bytes"]
    digest = hashlib.sha256()
    with destination.open("xb") as output:
        while remaining:
            contents = stream.read(min(remaining, 1024 * 1024))
            if not contents:
                raise ValueError("发行文件被截断")
            output.write(contents)
            digest.update(contents)
            remaining -= len(contents)
    if digest.hexdigest() != artifact["sha256"]:
        raise ValueError("发行文件摘要校验失败")
    executable = artifact["path"] in {"dever-core", "bootstrap/dever", "bootstrap/deverd"}
    destination.chmod(0o755 if executable else 0o644)


def payload(release, source, version, platform, catalog, trusted_key=None):
    if source:
        for name, artifact in catalog.items():
            path = source / name
            for ancestor in (path, *path.parents):
                if ancestor.is_symlink():
                    raise ValueError("本地发行文件不能经过符号链接")
                if ancestor == source:
                    break
            if not path.is_file() or path.stat().st_size != artifact["bytes"]:
                raise ValueError("本地发行文件类型或长度错误")
            with path.open("rb") as stream:
                copy_artifact(stream, release / name, artifact)
        return
    if trusted_key is None:
        raise ValueError("网络发行解压需要独立信任公钥")
    # Only signed bytes are executable. Keep the helper separate so Rust can
    # create_new every archive member and enforce one complete codec/TAR contract.
    with tempfile.TemporaryDirectory(prefix=".extract-", dir=release.parent) as directory:
        scratch = Path(directory)
        helper = scratch / "helper"
        base = f"{RELEASES}/download/v{version}/dever-{platform}"
        for name, artifact in catalog.items():
            if name == "bootstrap/dever" or name.startswith("bootstrap/lib/"):
                with download(f"{base}.blob-{artifact['sha256']}") as stream:
                    copy_artifact(stream, helper / name, artifact)
                    if stream.read(1):
                        raise ValueError("bootstrap 下载超过签名长度")
        compressed = scratch / "base.tar.zst"
        download_archive(f"{base}.tar.zst", compressed)
        configuration = scratch / "extract.json"
        configuration.write_text(json.dumps({
            "release": str(release), "archive": str(compressed),
            "trusted_key": str(trusted_key),
        }))
        subprocess.run([str(helper / "bootstrap/dever"), "--dever-extract", str(configuration)],
                       env={}, check=True, timeout=180)


def download_archive(address, destination):
    remaining = MAX_RELEASE
    with download(address) as stream, destination.open("xb") as output:
        while contents := stream.read(min(remaining + 1, 1024 * 1024)):
            remaining -= len(contents)
            if remaining < 0:
                raise ValueError("发行下载超过 2 GiB")
            output.write(contents)


def install(arguments):
    if os.geteuid() != 0:
        raise ValueError("机器安装需要管理员权限；先检查脚本，再用 sudo python3 执行")
    platform = platform_name()
    if arguments.version != "latest" and not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", arguments.version):
        raise ValueError("--version 需要 latest 或准确版本")
    system_root = arguments.system_root.absolute()
    if not system_root.is_dir() or system_root.is_symlink():
        raise ValueError("--system-root 必须是已存在的真实目录")
    source = arguments.release.absolute() if arguments.release else None
    if source and (not source.is_dir() or source.is_symlink()):
        raise ValueError("--release 必须是已存在的真实发行目录")
    selection = "latest/download" if arguments.version == "latest" else f"download/v{arguments.version}"
    # The root-owned staging also keeps the pinned key outside the downloaded release.
    with tempfile.TemporaryDirectory(prefix=".dever-install-", dir=system_root) as directory:
        scratch = Path(directory)
        release = scratch / "release"
        release.mkdir()
        metadata(release, source, selection, platform)
        version, catalog, key = authenticate(release, arguments.trusted_key, scratch, platform, arguments.version)
        trusted = scratch / "release.pub"
        trusted.write_text(key.hex() + "\n")
        payload(release, source, version, platform, catalog, trusted)
        configuration = scratch / "config"
        configuration.mkdir()
        (configuration / "setting.json").write_text(json.dumps({
            "release": str(release), "system_root": str(system_root),
            "trusted_key": str(trusted),
            "activate_service": system_root == Path("/") and not arguments.no_start,
        }))
        subprocess.run([str(release / "bootstrap/dever"), "--dever-install", str(scratch)],
                       env={}, check=True, timeout=180)
    print(f"Dever {version} 已安装到 {system_root / 'opt/dever'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="latest")
    parser.add_argument("--release", type=Path, help="使用本地已签名发行目录，不下载")
    parser.add_argument("--trusted-key", type=Path, default=Path(__file__).resolve().parents[1] / "assets/release.pub")
    parser.add_argument("--system-root", type=Path, default=Path("/"), help="已有的自有安装镜像目录；默认安装当前机器")
    parser.add_argument("--no-start", action="store_true", help="不启动当前机器 systemd 服务")
    arguments = parser.parse_args()
    try:
        install(arguments)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Dever 安装失败：{error}\n")


if __name__ == "__main__":
    main()
