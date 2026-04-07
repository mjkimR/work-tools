"""
api_spec.py
-----------
taiga_api.py 의 --help 출력을 파싱하여 references/api_spec.md 를 자동 생성하는 스크립트.
subparsers 정의를 복사하지 않고, subprocess 로 --help 를 실행해 그 결과를 그대로 사용한다.

실행 방법:
    cd task-writer/misc
    python api_spec.py
"""

import re
import subprocess
import sys
from pathlib import Path

# ── 경로 설정 ────────────────────────────────────────────────────────────────
MISC_DIR = Path(__file__).parent
SCRIPTS_DIR = MISC_DIR.parent / "scripts"
REFERENCES_DIR = MISC_DIR.parent / "references"
OUTPUT_FILE = REFERENCES_DIR / "api_spec.md"
TAIGA_API = str(SCRIPTS_DIR / "taiga_api.py")


# ── help 실행 헬퍼 ────────────────────────────────────────────────────────────


def _run_help(*args) -> str:
    """taiga_api.py [args] --help 를 실행하고 stdout 을 반환한다."""
    result = subprocess.run(
        [sys.executable, TAIGA_API, *args, "--help"],
        capture_output=True,
        text=True,
        cwd=str(SCRIPTS_DIR),
    )
    return (result.stdout or result.stderr).strip()


def _extract_subcommands(top_help: str) -> list[str]:
    """top-level help 에서 서브커맨드 이름 목록을 추출한다."""
    commands = []
    in_block = False
    for line in top_help.splitlines():
        stripped = line.strip()
        # argparse 는 {cmd1,cmd2,...} 또는 positional 블록으로 나열한다
        if re.match(r"\{.+\}", stripped):
            names = re.findall(r"[\w-]+", stripped)
            commands.extend(names)
            break
        if stripped in ("positional arguments:", "{"):
            in_block = True
            continue
        if in_block:
            if stripped.startswith("-") or stripped == "":
                continue
            m = re.match(r"^([\w-]+)", stripped)
            if m:
                commands.append(m.group(1))
    return commands


# ── Markdown 생성 ─────────────────────────────────────────────────────────────


def _build_markdown(top_help: str, subcommands: list[str], sub_helps: dict[str, str]) -> str:
    lines: list[str] = []

    lines.append("# Taiga API CLI – Command Reference")
    lines.append("")
    lines.append("이 파일은 `misc/api_spec.py` 에 의해 자동 생성됩니다.")
    lines.append("직접 수정하지 말고, taiga_api.py 수정 후 재생성하세요.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 커맨드 목록
    lines.append("## Commands")
    lines.append("")
    for cmd in subcommands:
        lines.append(f"- {cmd}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 각 커맨드 상세
    for cmd in subcommands:
        lines.append(f"## {cmd}")
        lines.append("")
        lines.append("```")
        lines.append(sub_helps[cmd])
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


# ── 메인 ─────────────────────────────────────────────────────────────────────


def main():
    print("taiga_api.py --help 수집 중...")
    top_help = _run_help()

    # {list-projects,search-userstories,...} 형태에서 커맨드 추출
    m = re.search(r"\{([\w,\-]+)\}", top_help)
    if not m:
        print("ERROR: 서브커맨드 목록을 찾을 수 없습니다.", file=sys.stderr)
        print(top_help)
        sys.exit(1)
    subcommands = m.group(1).split(",")

    sub_helps: dict[str, str] = {}
    for cmd in subcommands:
        print(f"  {cmd} --help 수집 중...")
        sub_helps[cmd] = _run_help(cmd)

    md_content = _build_markdown(top_help, subcommands, sub_helps)

    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(md_content, encoding="utf-8")
    print(f"✅  api_spec.md 생성 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
