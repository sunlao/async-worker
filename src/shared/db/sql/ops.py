class Ops:
    ops_ledger_cnt = "select count(*) cnt from raw.ops_ledger"

    def get(self, p_name: str) -> str:
        return getattr(self, p_name)
