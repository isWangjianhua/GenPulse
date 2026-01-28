from sqladmin import Admin, ModelView
from genpulse.infra.database.models import Task

class TaskAdmin(ModelView, model=Task):
    column_list = [
        Task.task_id, 
        Task.task_type, 
        Task.status, 
        Task.created_at, 
        Task.progress
    ]
    column_searchable_list = [Task.task_id, Task.task_type]
    column_sortable_list = [Task.created_at, Task.status]
    column_default_sort = ("created_at", True)
    
    name = "Task"
    name_plural = "Tasks"
    icon = "fa-solid fa-list-check"
    
    # Detail view settings
    column_details_list = [
        Task.task_id,
        Task.task_type,
        Task.status,
        Task.progress,
        Task.created_at,
        Task.updated_at,
        Task.params,
        Task.result
    ]
    
    # Permissions
    can_create = False  # Tasks should be created via API flows
    can_edit = False    # Tasks logs are generally immutable
    can_delete = True   # Admin can clean up old tasks
    can_view_details = True

def init_admin(app, engine):
    """Initialize SQLAdmin dashboard."""
    admin = Admin(app, engine, title="GenPulse Admin")
    admin.add_view(TaskAdmin)
    return admin
