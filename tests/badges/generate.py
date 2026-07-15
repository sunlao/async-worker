from os import getcwd, mkdir, remove
from os.path import join, isdir, isfile
from subprocess import Popen, PIPE
from anybadge import Badge
from badges.errors import ProcessExecutionFailure, PyLintScoreFailure


class Generate:  # pylint: disable=too-many-instance-attributes
    def __init__(self):
        cwd = getcwd()
        self.coverage_path = join(cwd, "docs", "code_coverage")
        self._check_folder()
        self.lint_threshold = {2: "red", 4: "orange", 6: "yellow", 10: "green"}
        self.py_lint_command = "pylint src --rcfile=tox.ini"
        self.score_search_1 = "rated at "
        self.score_search_2 = "/"

    def _check_badge(self, badge):
        path = join(self.coverage_path, badge)
        if isfile(path):
            remove(path)

    def _check_folder(self):
        if isdir(self.coverage_path) is False:
            mkdir(self.coverage_path)

    def _cli(self, p_command):
        with Popen(
            [p_command], shell=True, universal_newlines=True, stdout=PIPE
        ) as process_obj:
            process_obj.wait()
            code = process_obj.returncode
            output = process_obj.stdout.read()
        return {"code": code, "output": output}

    def _lint_badge(self, p_score):
        self._check_badge("pylint.svg")
        badge = Badge("pylint", p_score, thresholds=self.lint_threshold)
        try:
            badge.write_badge(f"{self.coverage_path}/pylint.svg")
        except RuntimeError as e:
            if "already exists" not in str(e).lower():
                raise

    def _score(self, p_output):
        pre_index1 = p_output.find(self.score_search_1)
        index1 = pre_index1 + len(self.score_search_1)
        index2 = p_output.find(self.score_search_2)
        return p_output[index1:index2]

    def black(self):
        self._check_badge("black.svg")
        badge = Badge("CodeFormat", "Black", default_color="#000000")
        badge.write_badge(f"{self.coverage_path}/black.svg")

    def code_style(self):
        self._check_badge("CodeStyle.svg")
        badge = Badge("CodeStyle", "pass", default_color="#0CEDDE")
        try:
            badge.write_badge(f"{self.coverage_path}/CodeStyle.svg")
        except RuntimeError as e:
            if "already exists" not in str(e).lower():
                raise

    def pylint(self):
        result = self._cli(self.py_lint_command)
        print(f"src: pylint output: {result['output']}")
        if result["code"] != 0:
            raise ProcessExecutionFailure("pylint", result["code"], result["output"])
        score = self._score(result["output"])
        if score != "10.00":
            raise PyLintScoreFailure(score)
        self._lint_badge(score)

    def safety(self):
        self._check_badge("bandit.svg")
        badge1 = Badge("Bandit", "pass", default_color="#0040FF")
        badge1.write_badge(f"{self.coverage_path}/bandit.svg")
        self._check_badge("safety.svg")
        badge2 = Badge("pip-audit", "pass", default_color="#2D03C3D3")
        badge2.write_badge(f"{self.coverage_path}/safety.svg")
