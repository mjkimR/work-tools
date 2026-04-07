import os
import re
import subprocess
import sys


# Simple .env loader (taiga_api.py와 동일한 방식)
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        key, value = parts
                        os.environ[key] = value


load_env()

GIT_USER_EMAIL = os.environ.get("GIT_USER_EMAIL", "")
GIT_TARGET_REPO = os.environ.get("GIT_TARGET_REPO", "")


def parse_commit_range(input_str: str) -> tuple[str, str | None]:
    """
    커밋 입력을 파싱합니다.
    - 단일 커밋: "abc1234"           → ("abc1234", None)
    - 범위 (..):  "abc1234..def5678" → ("abc1234", "def5678")
    - 범위 (~N):  "abc1234~3"        → HEAD~3 느낌으로 abc1234^^^을 시작으로
                                       실제로는 "abc1234~3..abc1234" 로 처리
    """
    input_str = input_str.strip()

    # "SHA..SHA" 형식
    if ".." in input_str:
        parts = input_str.split("..", 1)
        return parts[0].strip(), parts[1].strip()

    # "SHA~N" 형식
    tilde_match = re.match(r"^([0-9a-fA-F]+)~(\d+)$", input_str)
    if tilde_match:
        sha = tilde_match.group(1)
        n = tilde_match.group(2)
        return f"{sha}~{n}", sha

    # 단일 커밋
    return input_str, None


def get_git_log(repo_path: str, start: str, end: str | None, author_email: str) -> list[dict]:
    """
    git log를 가져옵니다.
    단일 커밋이면 해당 커밋 1개만, 범위면 start..end 사이 커밋들을 반환합니다.
    author_email 로 필터링합니다.
    """
    if end is None:
        # 단일 커밋 조회
        rev_range = [start]
        extra_flags = ["-n", "1"]
    else:
        # 범위 조회: start..end (start 제외, end 포함)
        rev_range = [f"{start}..{end}"]
        extra_flags = []

    cmd = [
        "git",
        "-C",
        repo_path,
        "log",
        "--author",
        author_email,
        "--pretty=format:%H%x00%an%x00%ae%x00%ad%x00%s%x00%b%x00END",
        "--date=iso",
        *extra_flags,
        *rev_range,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"git log 실행 오류:\n{result.stderr.strip()}")

    raw = result.stdout.strip()
    if not raw:
        return []

    commits = []
    # END 구분자로 각 커밋 블록 분리
    for block in raw.split("\x00END"):
        block = block.strip()
        if not block:
            continue
        parts = block.split("\x00")
        if len(parts) < 5:
            continue
        sha, author_name, author_email_val, date, subject = parts[0], parts[1], parts[2], parts[3], parts[4]
        body = parts[5].strip() if len(parts) > 5 else ""
        commits.append(
            {
                "sha": sha,
                "author_name": author_name,
                "author_email": author_email_val,
                "date": date,
                "subject": subject,
                "body": body,
            }
        )

    return commits


def get_commit_diff(repo_path: str, sha: str) -> str:
    """특정 커밋의 diff(변경사항)를 가져옵니다."""
    cmd = ["git", "-C", repo_path, "show", "--stat", "--patch", sha]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git show 오류 ({sha}):\n{result.stderr.strip()}")
    return result.stdout.strip()


def fetch_commits_with_diff(repo_path: str, commit_input: str, author_email: str) -> list[dict]:
    """
    커밋 입력(단일 or 범위)을 받아 각 커밋의 로그 + diff를 반환합니다.
    """
    start, end = parse_commit_range(commit_input)
    commits = get_git_log(repo_path, start, end, author_email)

    if not commits:
        print(f"[경고] '{author_email}' 작성자의 커밋을 찾을 수 없습니다.")
        return []

    for commit in commits:
        commit["diff"] = get_commit_diff(repo_path, commit["sha"])

    return commits


def print_commits(commits: list[dict]) -> None:
    """커밋 정보를 보기 좋게 출력합니다."""
    for i, c in enumerate(commits, 1):
        print(f"\n{'=' * 60}")
        print(f"[{i}/{len(commits)}] {c['sha'][:12]}  {c['date']}")
        print(f"Author : {c['author_name']} <{c['author_email']}>")
        print(f"Subject: {c['subject']}")
        if c["body"]:
            print(f"Body   :\n{c['body']}")
        print("\n--- diff ---")
        print(c["diff"])


def main():
    if not GIT_TARGET_REPO:
        print("[오류] .env에 GIT_TARGET_REPO가 설정되어 있지 않습니다.", file=sys.stderr)
        sys.exit(1)

    if not GIT_USER_EMAIL:
        print("[오류] .env에 GIT_USER_EMAIL이 설정되어 있지 않습니다.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("사용법:")
        print("  단일 커밋 : python git_log.py <SHA>")
        print("  범위 (..): python git_log.py <SHA1>..<SHA2>")
        print("  범위 (~N): python git_log.py <SHA>~<N>")
        sys.exit(1)

    commit_input = sys.argv[1]

    print(f"레포지토리 : {GIT_TARGET_REPO}")
    print(f"필터 이메일: {GIT_USER_EMAIL}")
    print(f"커밋 입력  : {commit_input}")

    try:
        commits = fetch_commits_with_diff(GIT_TARGET_REPO, commit_input, GIT_USER_EMAIL)
    except RuntimeError as e:
        print(f"[오류] {e}", file=sys.stderr)
        sys.exit(1)

    if not commits:
        print("조건에 맞는 커밋이 없습니다.")
        sys.exit(0)

    print(f"\n총 {len(commits)}개의 커밋을 찾았습니다.")
    print_commits(commits)


if __name__ == "__main__":
    main()
