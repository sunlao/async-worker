from shared.db.sql.hello import Hello
from shared.db.sql.admin import Admin
from shared.db.sql.natal import Natal
from shared.db.sql.ops import Ops


class Query:
    """Wrapper to get sql by name"""

    def get(self, p_name: str) -> str:
        # add SQL classes below to integrate sql with db init
        if p_name.startswith("hello"):
            sql = Hello().get(p_name)
            return sql
        if p_name.startswith("admin"):
            sql = Admin().get(p_name)
            return sql
        if p_name.startswith("natal"):
            sql = Natal().get(p_name)
            return sql
        if p_name.startswith("ops"):
            sql = Ops().get(p_name)
            return sql
        return None
