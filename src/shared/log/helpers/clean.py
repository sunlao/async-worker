import re

# precompiled patterns (case-insensitive where needed)
_AUTH_BEARER = re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s,;]+)")
_KV_SECRET = re.compile(
    r"(?i)\b(api_key|apikey|access_token|token|secret|password|pwd)\s*(=|:)\s*([^\s&;,]+)"
)
_URL_CREDS = re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://[^/\s:@]+:)([^@\s/]+)(@)")
_JWT = re.compile(r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
_AWS_AKID = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # keep \t and \n


def sanitize_str(s: str, max_len: int = 2000) -> str:
    # normalize whitespace + drop control chars (except \n, \t)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _CONTROL.sub("", s)

    # targeted masking
    s = _AUTH_BEARER.sub(r"\1***", s)  # Authorization: Bearer ***
    s = _KV_SECRET.sub(lambda m: f"{m.group(1)}{m.group(2)}***", s)  # key=value -> ***
    s = _URL_CREDS.sub(r"\1***\3", s)  # scheme://user:***@host
    s = _JWT.sub("***jwt***", s)  # JWT tokens
    s = _AWS_AKID.sub("***aws_key***", s)  # AWS access key id

    # middle-elide to bound size
    if len(s) > max_len:
        marker = " …[truncated]… "
        keep = max_len - len(marker)
        head = keep // 2
        tail = keep - head
        s = s[:head] + marker + s[-tail:]
    return s
