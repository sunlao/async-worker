# pylint: disable=line-too-long
import pathlib
import re
import fnmatch

# Files with # edge-allow: {pattern} at the top of file are excluded. They are meant
# as manual exceptions for python when something is doing execution and not policy
#
# For example src/shared/log/helper/gzip.py has # edge-allow: open
# It is only using gz_open for execution not policy
#
# Manual exceptions should be rare and documented with a justification.


# root of your source
SRC = pathlib.Path("src")

# Exdges exceptionlist: is meant only for files that are edges
EDGES = {
    "src/worker/__init__.py",  # arq control plane
    "src/api/main.py",  # fast api control plan
    "src/shared/config/locker.py",  # edge for getting configs and managning secrets
    "src/quiesce/queue.py",  # quiesce - only ran during maintenance
    "src/quiesce/control.py",  # quiesce - only ran during maintenance
    "src/quiesce/gate.py",  # quiesce - only ran during maintenance
}


def is_whitelisted(path: pathlib.Path) -> bool:
    p = path.as_posix()
    return any(fnmatch.fnmatch(p, pat) for pat in EDGES)


# forbidden patterns
# fmt: off
PATTERNS = {
    # Env / config
    "getenv":              r"\bgetenv\b",
    "os.environ":          r"os\.environ",

    # Time / clock
    "datetime.now":        r"datetime\.now\(",
    "datetime.today":      r"datetime\.today\(",
    "time.time":           r"time\.time\(",
    "time.sleep":          r"time\.sleep\(",
    "asyncio.sleep":       r"(?:asyncio\.sleep\(|from\s+asyncio\s+import\s+sleep)",
    "asyncio.wait_for":    r"asyncio\.wait_for\(",

    # Randomness / secrets
    "uuid":                r"uuid\.uuid",
    "random":              r"random\.",
    "secrets":             r"(?:secrets\.|from\s+secrets\s+import)",

    # IO / sys
    "open":                r"\bopen\(",
    "print":               r"\bprint\(",
    "sys.stdout":          r"sys\.stdout",
    "sys.stderr":          r"sys\.stderr",

    # Filesystem path policy (edge-only)
    "pathlib":             r"(?m)^\s*(?:import\s+pathlib\b|from\s+pathlib\s+import\b)|pathlib\.Path\b|(?<!\w)Path\s*\(",
    "os.path":             r"\bos\.path\.",

    "tempfile":            r"(?m)^\s*(?:import\s+tempfile\b|from\s+tempfile\s+import\b)|\btempfile\.",
    "subprocess":          r"(?m)^\s*(?:import\s+subprocess\b|from\s+subprocess\s+import\b)|\bsubprocess\.",
    "shutil.copy":         r"(?m)^\s*(?:import\s+shutil\b|from\s+shutil\s+import\b)|\bshutil\.copy\b",
    "shutil.move":         r"(?m)^\s*(?:import\s+shutil\b|from\s+shutil\s+import\b)|\bshutil\.move\b",
    "os.chmod":            r"\bos\.chmod\b",
    "os.chown":            r"\bos\.chown\b",
    "os.stat":             r"\bos\.stat\b",

    # Networking / clients (policy: edge-only)
    "requests":            r"(?m)^\s*(?:import\s+requests\b|from\s+requests\s+import\b)|\brequests\.",
    "httpx":               r"(?m)^\s*(?:import\s+httpx\b|from\s+httpx\s+import\b)|\bhttpx\.",
    "aiohttp":             r"(?m)^\s*(?:import\s+aiohttp\b|from\s+aiohttp\s+import\b)|\baiohttp\b",
    "http.client":         r"(?m)^\s*(?:import\s+http\.client\b|from\s+http\s+import\s+client\b)|\bhttp\.client\b",
    "ftplib":              r"(?m)^\s*(?:import\s+ftplib\b|from\s+ftplib\s+import\b)|\bftplib\b",
    "smtplib":             r"(?m)^\s*(?:import\s+smtplib\b|from\s+smtplib\s+import\b)|\bsmtplib\b",
    "ssl":                 r"(?m)^\s*(?:import\s+ssl\b|from\s+ssl\s+import\b)|\bssl\b",

    # DB / brokers (policy: edge-only)
    "asyncpg.connect":     r"\basyncpg\.connect\b",
    "databases.Database":  r"\bdatabases\.Database\b",
    "postgres_uri":        r"postgres://",
    "redis_uri":           r"redis://",
    "sqlalchemy":          r"(?m)^\s*(?:import\s+sqlalchemy\b|from\s+sqlalchemy\s+import\b)|\bsqlalchemy\b",
    "kafka":               r"(?m)^\s*(?:import\s+kafka\b|from\s+kafka\s+import\b)|\bkafka\b",
    "pika":                r"(?m)^\s*(?:import\s+pika\b|from\s+pika\s+import\b)|\bpika\b",
    "kombu":               r"(?m)^\s*(?:import\s+kombu\b|from\s+kombu\s+import\b)|\bkombu\b",

    # System identity
    "socket.gethostname":  r"\bsocket\.gethostname\b",
    "os.getpid":           r"\bos\.getpid\b",
    "platform":            r"(?m)^\s*(?:import\s+platform\b|from\s+platform\s+import\b)|\bplatform\.",
    "getpass":             r"(?m)^\s*(?:import\s+getpass\b|from\s+getpass\s+import\b)|\bgetpass\b",
    "os.getlogin":         r"\bos\.getlogin\b",
    "os.uname":            r"\bos\.uname\b",

    # Process / concurrency
    "sys.argv":            r"\bsys\.argv\b",
    "sys.exit":            r"\bsys\.exit\b",
    "logging.basicConfig": r"\blogging\.basicConfig\b",
    "signal":              r"(?m)^\s*(?:import\s+signal\b|from\s+signal\s+import\b)|\bsignal\.signal\b",
    "multiprocessing":     r"(?m)^\s*(?:import\s+multiprocessing\b|from\s+multiprocessing\s+import\b)|\bmultiprocessing\.",
    "threading":           r"(?m)^\s*(?:import\s+threading\b|from\s+threading\s+import\b)|\bthreading\.",
    "concurrent.futures":  r"(?m)^\s*(?:import\s+concurrent\.futures\b|from\s+concurrent\.futures\s+import\b)|\bconcurrent\.futures\b",

    # Cloud SDKs
    "boto3":               r"(?m)^\s*(?:import\s+boto3\b|from\s+boto3\s+import\b)|\bboto3\b",
    "google.cloud":        r"(?m)^\s*(?:import\s+google\.cloud\b|from\s+google\.cloud\s+import\b)|\bgoogle\.cloud\b",
    "azure":               r"(?m)^\s*(?:import\s+azure\b|from\s+azure\s+import\b)|\bazure\b",

    # Serialization / templating
    "jinja2":              r"(?m)^\s*(?:import\s+jinja2\b|from\s+jinja2\s+import\b)|\bjinja2\b",
    "yaml.safe_load":      r"(?m)^\s*(?:import\s+yaml\b|from\s+yaml\s+import\b)|\byaml\.safe_load\b",
    "pickle.load":         r"(?m)^\s*(?:import\s+pickle\b|from\s+pickle\s+import\b)|\bpickle\.load\b",
    "pickle.loads":        r"\bpickle\.loads\b",
    "marshal.load":        r"(?m)^\s*(?:import\s+marshal\b|from\s+marshal\s+import\b)|\bmarshal\.load\b",
    "marshal.loads":       r"\bmarshal\.loads\b",
}
# fmt: on


def allowed_names(path: pathlib.Path) -> set[str]:
    try:
        head = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:8]
    except Exception:  # pylint: disable=broad-exception-caught
        return set()
    for line in head:
        s = line.strip()
        if s.startswith("# edge-allow:"):
            rhs = s.split(":", 1)[1]
            return {name.strip() for name in rhs.split(",") if name.strip()}
    return set()


def test_edge_only_code():
    bad = []
    for py in SRC.rglob("*.py"):
        if is_whitelisted(py):
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        allowed = allowed_names(py)
        for name, regex in PATTERNS.items():
            if name in allowed:
                continue
            if re.search(regex, text):
                bad.append((py.as_posix(), name))
    assert not bad, f"Edge-only patterns found:\n{bad}"
