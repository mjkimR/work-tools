import subprocess
from urllib.parse import urlparse

from core.exception import TokenRetrievalError


def get_session_info(target_domain, fields=("auth_token", "token")):
    """
    Extract auth token and base URL from Google Chrome using AppleScript.
    Returns (token, base_url) or raises TaigaTokenError with a detailed message.
    """
    token_field = " || ".join([f"window.localStorage.getItem('{field}')" for field in fields])
    applescript = f'''
    tell application "Google Chrome"
        set foundInfo to "NOT_FOUND"
        repeat with w in windows
            repeat with t in tabs of w
                set currentURL to URL of t
                if currentURL contains "{target_domain}" then
                    set foundToken to execute t javascript "{token_field};"
                    if foundToken is not "NOT_FOUND" and foundToken is not missing value and foundToken is not "null" then
                        set foundInfo to foundToken & "|" & currentURL
                        exit repeat
                    end if
                end if
            end repeat
            if foundInfo is not "NOT_FOUND" then exit repeat
        end repeat
        return foundInfo
    end tell
    '''

    try:
        result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)

        if result.returncode != 0:
            stderr_msg = result.stderr.strip()
            if "자바스크립트 허용" in stderr_msg or "Allow JavaScript" in stderr_msg or "Apple Events" in stderr_msg:
                raise TokenRetrievalError(
                    "Chrome에서 AppleScript JavaScript 실행이 비활성화되어 있습니다.\n"
                    "Chrome 메뉴 → 보기 → 개발자 → 'Apple Events의 자바스크립트 허용' 을 체크해주세요."
                )
            raise TokenRetrievalError(f"AppleScript 실행 오류: {stderr_msg}")

        output = result.stdout.strip()

        if output == "NOT_FOUND" or not output:
            raise TokenRetrievalError(
                f"Chrome에서 '{target_domain}' 도메인의 탭을 찾을 수 없습니다.\n"
                "Chrome에서 해당 탭에 로그인되어 있는지 확인해주세요."
            )

        token, tab_url = output.split("|", 1)

        # Determine base_url from tab_url
        parsed = urlparse(tab_url)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc
        base_url = f"{scheme}://{netloc}/api/v1"
        return token.strip('"'), base_url
    except TokenRetrievalError:
        raise
    except Exception as e:
        raise TokenRetrievalError(f"Chrome 세션 정보 추출 중 예상치 못한 오류 발생: {e}") from e
