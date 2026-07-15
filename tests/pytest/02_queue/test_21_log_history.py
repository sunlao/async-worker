from datetime import datetime, timezone
from uuid import uuid4
from shared.models.api import LedgerData
from shared.helper.ops_ledger import OpsLedger as OL


async def test_ledger(arq_client, db, db_get_one):
    ledger = await arq_client.ledger(datetime(1970, 1, 1, tzinfo=timezone.utc))
    assert len(ledger) > 0
    for dto in ledger:
        assert LedgerData.model_validate(dto)

    ol = OL(arq_client, db, uuid4)
    await ol.load()
    row = await db_get_one("ops_ledger_cnt")
    assert row[0] >= 1
