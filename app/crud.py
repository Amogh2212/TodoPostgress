from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timezone

def get_todos(db: Session):
    return db.query(models.Todo).all()

def get_todo(db: Session, todo_id: int):
    return db.query(models.Todo).filter(models.Todo.id == todo_id).first()

def update_todo(db: Session, todo_id: int, todo_update: schemas.TodoCreate):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()

    if db_todo:
        # Track completion timestamp
        if todo_update.completed and not db_todo.completed:
            db_todo.completed_at = datetime.now(timezone.utc)
        elif not todo_update.completed:
            db_todo.completed_at = None

        # Update all fields
        db_todo.title = todo_update.title
        db_todo.description = todo_update.description
        db_todo.urgency = todo_update.urgency
        db_todo.category = todo_update.category
        db_todo.completed = todo_update.completed

        db.commit()
        db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: int):
    db_todo = get_todo(db, todo_id)
    if db_todo:
        db.delete(db_todo)
        db.commit()
    return db_todo
