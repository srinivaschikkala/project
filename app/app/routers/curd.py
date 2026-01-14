"""CRUD operations"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.sql import get_db, create_item, get_item, update_item, delete_record
from app.core.auth import get_current_user

from mysql.connector import Error
from fastapi import Request

router = APIRouter()
from dotenv import load_dotenv


# Get records
@router.get("/db/{table_name}")
async def get_records(
    request: Request,
    table_name: str = "users",
    db=Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    query = f"select * from {table_name} limit 100"
    try:
        cursor = db.cursor(dictionary=True)  # To return rows as dictionaries
        cursor.execute(query)
        records = cursor.fetchall()

        if not records:
            raise HTTPException(status_code=404, detail=f"No records found in table")

        return {"records": records}
    except Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving records: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()


# Insert single
@router.post("/db/{table_name}")
async def create_record(
    table_name: str,
    payload: dict,
    request: Request,
    db=Depends(get_db),
    current_user: str = Depends(get_current_user),
):

    if not payload:
        raise HTTPException(status_code=400, detail="Payload cannot be empty")
    result = create_item(payload, table_name, db)
    return result


# Get single
@router.get("/db/{table_name}/{id}")
async def get_record_by_id(
    id: int,
    table_name: str,
    request: Request,
    db=Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    query = f"SELECT * FROM {table_name} where id={id}"
    result = get_item(query, db)
    return result


# Single update
@router.put("/db/{table_name}/{record_id}")
async def update_record_by_id(
    table_name: str,
    record_id: int,
    payload: dict,
    request: Request,
    db=Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    if not payload:
        raise HTTPException(status_code=400, detail="Payload cannot be empty")

    result = update_item(payload, table_name, record_id, db)
    return result


@router.delete("/db/{table_name}/{id}")
async def delete_records(
    table_name: str,
    id: int,
    request: Request,
    db=Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = delete_record(id, table_name, db)
    return result
