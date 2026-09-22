"""sales collection"""

from pymongo.client_session import ClientSession

from app.infrastructure.mongo_client import get_database
from app.models.sale import Sale

COLLECTION_NAME = "sales"


def insert(sale: Sale, session: ClientSession) -> Sale:
    doc = sale.model_dump(by_alias=True, exclude={"id"})
    doc["change_given"] = {str(k): v for k, v in doc["change_given"].items()}

    result = get_database()[COLLECTION_NAME].insert_one(doc, session=session)

    doc["_id"] = str(result.inserted_id)
    doc["change_given"] = sale.change_given
    return Sale(**doc)
