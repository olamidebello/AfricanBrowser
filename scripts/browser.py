#!/usr/bin/env python3
"""Pinned Chromium source checkout, branding, compilation and artifact collection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from branding import ANDROID_NAME_FILE, apply, STRING_FILES, LITERAL_CHANGES, resource_files

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "config/upstream.json").read_text())
PLATFORMS = {
    "linux": ("Linux", "chromium", "chrome", "//chrome:chrome"),
    "windows": ("Windows", "chromium", "mini_installer", "//chrome/installer/mini_installer:mini_installer"),
    "macos": ("Darwin", "chromium", "chrome", "//chrome:chrome"),
    "android": ("Linux", "android", "chrome_public_apk", "//chrome/android:chrome_public_apk"),
    "ios": ("Darwin", "ios", "chrome", "//ios/chrome/app:chrome"),
}


def run(args, cwd, env=None, capture=False):
    print("+", subprocess.list2cmdline([str(a) for a in args]), flush=True)
    return subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                          check=True, text=True, stdout=subprocess.PIPE if capture else None)


def gn_args(target, cpu):
    args = ["is_debug=false", "is_component_build=false", "is_chrome_branded=false",
            "symbol_level=0", "use_remoteexec=false", "chrome_pgo_phase=0",
            f'target_cpu="{cpu}"']
    if target == "android":
        args += ['target_os="android"', 'chrome_public_manifest_package="org.africanbrowser.browser"',
                 'use_siso=false']
    if target == "ios":
        args += ['target_os="ios"', 'target_environment="simulator"',
                 "ios_enable_code_signing=false", 'ios_app_bundle_id_prefix="org.africanbrowser"']
    return "\n".join(args) + "\n"


def doctor(target, work, minimum_free=100):
    problems = []
    expected = PLATFORMS[target][0]
    if platform.system() != expected:
        problems.append(f"{target} requires a {expected} host; this host is {platform.system()}")
    existing = work
    while not existing.exists():
        existing = existing.parent
    free = shutil.disk_usage(existing).free / 1024**3
    print(f"Free disk: {free:.1f} GiB; provision at least 200 GiB for a build worker.")
    if free < minimum_free:
        problems.append(f"Need at least {minimum_free} GiB free for this stage (200+ GiB recommended for a fresh worker)")
    if shutil.which("git") is None:
        problems.append("Git is not installed")
    if target in ("macos", "ios") and not shutil.which("xcodebuild"):
        problems.append("Install the Xcode version required by the pinned Chromium revision")
    if target == "windows":
        print("Windows requires the upstream-specified Visual Studio C++ toolchain and SDK.")
    for problem in problems:
        print("BLOCKED:", problem)
    return not problems


def tools_env(work):
    env = dict(os.environ)
    env["PATH"] = str(work / "depot_tools") + os.pathsep + env["PATH"]
    env["DEPOT_TOOLS_UPDATE"] = "0"
    if platform.system() == "Windows":
        env["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
    return env


def tool(work, name):
    suffix = ".bat" if platform.system() == "Windows" else ""
    return work / "depot_tools" / (name + suffix)


def bootstrap_tools(work):
    depot = work / 'depot_tools'
    env = tools_env(work)
    # Automatic repository updates stay disabled to preserve the pinned revision.
    # Bootstrap the runtime separately; gclient can run via vpython even when the
    # Python runtime used by gn/autoninja has not been initialized.
    if platform.system() == 'Windows':
        if not (depot / 'python3_bin_reldir.txt').is_file():
            run(['cmd', '/c', depot / 'bootstrap/win_tools.bat'], depot, env)
        python = depot / 'python3.bat'
    else:
        if not (depot / 'python3_bin_reldir.txt').is_file():
            run([depot / 'ensure_bootstrap'], depot, env)
        python = depot / 'python-bin/python3'
    run([python, '--version'], depot, env)


def checkout(args):
    work = args.work
    if not doctor(args.target, work):
        raise RuntimeError("Build worker prerequisites are not met")
    work.mkdir(parents=True, exist_ok=True)
    depot = work / "depot_tools"
    if not depot.exists():
        run(["git", "clone", LOCK["depot_tools_url"], depot], work)
    run(["git", "checkout", LOCK["depot_tools_revision"]], depot)
    bootstrap_tools(work)
    tree = work / args.target
    tree.mkdir(exist_ok=True)
    source = tree / "src"
    if source.exists():
        dirty = run(["git", "status", "--porcelain"], source, capture=True).stdout
        if dirty.strip():
            raise RuntimeError("Source has local changes. Use a fresh work directory; no automatic reset.")
    config = {
        "name": "src", "url": LOCK["source_url"], "deps_file": "DEPS",
        "managed": False, "custom_deps": {}, "custom_vars": {},
    }
    text = "solutions = " + repr([config]) + "\n"
    if args.target in ("android", "ios"):
        text += "target_os = " + repr([args.target]) + "\n"
    (tree / ".gclient").write_text(text)
    env = tools_env(work)
    run([tool(work, "gclient"), "sync", "--no-history", "--nohooks", "--revision",
         "src@" + LOCK["chromium_revision"]], tree, env)
    actual = run(["git", "rev-parse", "HEAD"], source, capture=True).stdout.strip()
    if actual != LOCK["chromium_revision"]:
        raise RuntimeError("Source revision does not match upstream lock")
    print("Checkout complete. Install upstream build dependencies, then run build.")


def build(args):
    from logo_assets import apply as apply_logo, ICON_ROOTS
    if not doctor(args.target, args.work, minimum_free=40):
        raise RuntimeError("Build worker prerequisites are not met")
    source = args.work / args.target / "src"
    actual = run(["git", "rev-parse", "HEAD"], source, capture=True).stdout.strip()
    if actual != LOCK["chromium_revision"]:
        raise RuntimeError("Source revision does not match upstream lock")
    allowed = {"chrome/app/theme/chromium/BRANDING", *STRING_FILES, *LITERAL_CHANGES, ANDROID_NAME_FILE}
    allowed.update(str(p.relative_to(source)) for p in resource_files(source))
    changed = run(["git", "diff", "--name-only", "HEAD"], source, capture=True).stdout.splitlines()
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], source, capture=True).stdout.splitlines()
    unexpected = [name for name in changed if name not in allowed and
                  not any(name.startswith(folder + '/') for folder in ICON_ROOTS)]
    if unexpected or untracked:
        raise RuntimeError("Unreviewed source changes found; use a clean checkout")
    print("Branding:", apply(source))
    print("Logo resources:", apply_logo(source))
    env = tools_env(args.work)
    bootstrap_tools(args.work)
    run([tool(args.work, "gclient"), "runhooks"], source.parent, env)
    output = source / "out" / "AfricanBrowser"
    if args.checkpoint:
        if args.target != 'android' or platform.system() != 'Linux' or not args.segment_seconds:
            raise RuntimeError('Checkpoints require a bounded Android build on Linux')
        from build_checkpoint import normalize_inputs, restore
        identity = {'upstream': LOCK['chromium_revision'], 'target': args.target,
                    'cpu': args.cpu, 'gn_args': gn_args(args.target, args.cpu),
                    'project_commit': run(['git', 'rev-parse', 'HEAD'], ROOT, capture=True).stdout.strip()}
        normalize_inputs(source)
        restore(source, args.checkpoint, identity)
    output.mkdir(parents=True, exist_ok=True)
    (output / "args.gn").write_text(gn_args(args.target, args.cpu))
    run([tool(args.work, "gn"), "gen", "out/AfricanBrowser", "--fail-on-unused-args"], source, env)
    command = [tool(args.work, "autoninja"), "-C", "out/AfricanBrowser", PLATFORMS[args.target][2]]
    if args.jobs:
        command += ['-j', str(args.jobs)]
    if args.checkpoint:
        from build_checkpoint import bounded_compile, save
        complete = bounded_compile(command, source, env, args.segment_seconds)
        (ROOT / 'build-status.json').write_text(json.dumps({'complete': complete, 'identity': identity}) + '\n')
        if not complete:
            save(source, args.checkpoint, identity)
            print('Compilation checkpointed; another segment is required. No APK is claimed.')
            return
    else:
        run(command, source, env)
    print("Compilation finished. Run package, then perform the platform smoke tests.")


def package(args):
    from legal_assets import LEGAL_FILES
    source = args.work / args.target / "src"
    output = source / "out/AfricanBrowser"
    dest = ROOT / "dist" / f'AfricanBrowser-{LOCK["version"]}-{args.target}-{args.cpu}'
    if dest.exists():
        raise RuntimeError(f"Artifact directory already exists: {dest}")
    dest.mkdir(parents=True)
    if args.target == "android":
        shutil.copy2(output / "apks/ChromePublic.apk", dest / "AfricanBrowser.apk")
    elif args.target == "windows":
        shutil.copy2(output / "mini_installer.exe", dest / "AfricanBrowserSetup.exe")
    elif args.target in ("macos", "ios"):
        apps = list(output.glob("*.app"))
        if len(apps) != 1:
            raise RuntimeError(f"Expected exactly one app bundle, found {apps}")
        # ditto preserves bundle resource forks, permissions and symbolic links.
        run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", apps[0],
             dest / "AfricanBrowser.zip"], source)
    else:
        result = run([tool(args.work, "gn"), "desc", "out/AfricanBrowser",
                      PLATFORMS[args.target][3], "runtime_deps"], source,
                     tools_env(args.work), capture=True)
        dependencies = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not dependencies:
            raise RuntimeError("Unexpected GN runtime dependency manifest")
        payload = dest / "AfricanBrowser"
        payload.mkdir()
        for name in dependencies:
            relative = Path(name)
            src = (output / relative).resolve()
            if not src.is_relative_to(output.resolve()):
                raise RuntimeError(f"Runtime dependency outside build directory: {name}")
            target = payload / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, target, dirs_exist_ok=True, symlinks=True)
            else:
                shutil.copy2(src, target)
        shutil.make_archive(str(dest / "AfricanBrowser"), "gztar", dest, "AfricanBrowser")
        shutil.rmtree(payload)
    legal_dir = dest / 'legal'
    legal_dir.mkdir()
    for name in LEGAL_FILES:
        shutil.copy2(ROOT / name, legal_dir / name)
    shutil.copy2(source / 'LICENSE', legal_dir / 'Chromium-LICENSE')
    (dest / "build-info.json").write_text(json.dumps({
        "product": json.loads((ROOT / 'config/product.json').read_text()),
        "upstream": LOCK, "platform": args.target, "cpu": args.cpu,
        "ios_build": "simulator only" if args.target == "ios" else None,
        "release_status": "development; signing and browser acceptance tests required",
    }, indent=2) + "\n")
    checksums = []
    for path in sorted(dest.iterdir()):
        if path.is_file():
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            checksums.append(digest + "  " + path.name)
    (dest / "SHA256SUMS").write_text("\n".join(checksums) + "\n")
    print(dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "doctor", "checkout", "build", "package"])
    parser.add_argument("--target", choices=PLATFORMS, required=True)
    parser.add_argument("--cpu", choices=["x64", "arm64"], default="arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64")
    parser.add_argument("--work", type=Path, default=ROOT / "work")
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--segment-seconds', type=int)
    parser.add_argument('--jobs', type=int)
    args = parser.parse_args()
    args.work = args.work.resolve()
    if args.checkpoint:
        args.checkpoint = args.checkpoint.resolve()
    if " " in str(args.work):
        parser.error("Chromium build paths must not contain spaces")
    if args.target == "android" and args.cpu != "arm64":
        print("Note: use --cpu arm64 for modern Android phones; x64 is for emulators.")
    if args.command == "plan":
        print(json.dumps({"upstream": LOCK, "target": args.target,
                          "host": PLATFORMS[args.target][0], "gn_args": gn_args(args.target, args.cpu),
                          "build_target": PLATFORMS[args.target][2]}, indent=2))
    elif args.command == "doctor":
        return 0 if doctor(args.target, args.work) else 2
    else:
        globals()[args.command](args)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.CalledProcessError, OSError) as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
