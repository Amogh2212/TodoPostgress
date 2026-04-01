from sqlalchemy.orm import Session
from . import models, schemas
<<<<<<< HEAD
from datetime import datetime, timezone
=======
>>>>>>> dfd5a49fb15b43d667bf82569aa7f651b770411b

def get_todos(db: Session):
    return db.query(models.Todo).all()

def get_todo(db: Session, todo_id: int):
    return db.query(models.Todo).filter(models.Todo.id == todo_id).first()

def create_todo(db: Session, todo: schemas.TodoCreate):
    db_todo = models.Todo(**todo.dict())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

<<<<<<< HEAD
def update_todo(db: Session, todo_id: int, todo_update: schemas.TodoCreate):
    # 1. Find the existing task
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    
    if db_todo:
        # 2. Logic for completion timestamp
        # If the task is being marked as 'completed' for the first time
        if hasattr(todo_update, 'completed') and todo_update.completed == True:
            if not db_todo.completed:
                db_todo.completed_at = datetime.now(timezone.utc)
        
        # If the task is being marked as 'incomplete' again, clear the time
        elif hasattr(todo_update, 'completed') and todo_update.completed == False:
            db_todo.completed_at = None

        # 3. Update the other fields
        db_todo.title = todo_update.title
        db_todo.description = todo_update.description
        db_todo.urgency = todo_update.urgency
        # If your schema has 'completed', update it here too
        if hasattr(todo_update, 'completed'):
            db_todo.completed = todo_update.completed

=======
def update_todo(db: Session, todo_id: int, todo: schemas.TodoCreate):
    db_todo = get_todo(db, todo_id)
    if db_todo:
        for key, value in todo.dict().items():
            setattr(db_todo, key, value)
>>>>>>> dfd5a49fb15b43d667bf82569aa7f651b770411b
        db.commit()
        db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: int):
    db_todo = get_todo(db, todo_id)
    if db_todo:
        db.delete(db_todo)
        db.commit()
    return db_todo
