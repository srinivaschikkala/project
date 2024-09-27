from fastapi import HTTPException
import mysql.connector
from mysql.connector import Error
from os import environ


def get_db(application):

    try:
        if environ.get(f"{application.upper()}_APPNAME") == application:

            connection = mysql.connector.connect(
                host=environ.get(f"{application.upper()}_HOST"),
                user=environ.get(f"{application.upper()}_USER"),
                password=environ.get(f"{application.upper()}_PASSWORD"),
                database=environ.get(f"{application.upper()}_DB"),
            )
            return connection
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_item(query, db):

    cursor = db.cursor(dictionary=True)  # To return rows as dictionaries

    try:
        cursor.execute(query)
        record = cursor.fetchone()

        if not record:
            raise HTTPException(status_code=404, detail=f"No records found")

        return record
    except Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving records: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()


def create_item(payload, table_name, db):
    # Extract columns and values from the dictionary
    columns = payload.keys()
    placeholders = ", ".join(["%s"] * len(columns))
    column_names = ", ".join(columns)
    values = tuple(payload.values())
    query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

    cursor = db.cursor()

    try:
        cursor.execute(query, values)
        db.commit()
        return {"message": f"Inserted 1 record into {table_name}"}
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting record: {str(e)}")
    finally:
        cursor.close()
        db.close()


def delete_record(id, table_name, db):
    # Construct the WHERE clause from the criteria
    query = f"DELETE FROM {table_name} WHERE id = {id}"
    cursor = db.cursor()
    try:
        cursor.execute(query)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No records found matching the criteria in {table_name}",
            )

        return {"message": f"Deleted {cursor.rowcount} record(s) from {table_name}"}
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting records: {str(e)}")
    finally:
        cursor.close()
        db.close()


def insert_bulk(payload, table_name, db):

    # Extract columns and values from the first dict (assuming all records have the same structure)
    columns = payload[0].keys()
    placeholders = ", ".join(["%s"] * len(columns))
    column_names = ", ".join(columns)

    query = "insert into {table} ({columns}) values ({values});".format(
        table=table_name, columns=f"{column_names}", values=placeholders
    )

    values = []
    for record in payload:
        values.append(tuple(record.values()))

    cursor = db.cursor()

    try:
        cursor.executemany(query, values)
        db.commit()
        return {"message": f"Inserted {cursor.rowcount} records into {table_name}"}
    except Error as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error inserting records: {str(e)}"
        )
    finally:
        cursor.close()
        db.close()


def create_item(payload, table_name, db):
    # Extract columns and values from the dictionary
    columns = payload.keys()
    placeholders = ", ".join(["%s"] * len(columns))
    column_names = ", ".join(columns)
    values = tuple(payload.values())
    query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

    cursor = db.cursor()

    try:
        cursor.execute(query, values)
        db.commit()
        return {"message": f"Inserted 1 record into {table_name}"}
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting record: {str(e)}")
    finally:
        cursor.close()
        db.close()


def update_item(payload: dict, table_name: str, record_id: int, db):
    # Extract columns and values from the dictionary
    columns = payload.keys()
    set_clause = ", ".join([f"{col} = %s" for col in columns])
    values = tuple(payload.values()) + (record_id,)

    query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"  # Assuming 'id' is the primary key column

    cursor = db.cursor()

    try:
        cursor.execute(query, values)
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Record with id {record_id} not found in {table_name}",
            )
        return {"message": f"Updated record with id {record_id} in {table_name}"}
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating record: {str(e)}")
    finally:
        cursor.close()
        db.close()
