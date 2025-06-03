from math import log
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, ALL, MATCH, callback_context
from dash.exceptions import PreventUpdate
from datetime import datetime
import uuid
from croniter import croniter
from crontab import CronTab
import json
import os
import time # For a slight delay to help with ID uniqueness if needed


# --- App Initialization and Configuration ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA], suppress_callback_exceptions=True)
app.title = "Task Scheduler"

# --- Global Variables & Constants ---
tasks_data = []
TASKS_FILE_NAME = "tasks.json"
# Determine the directory of the currently running script to locate tasks.json
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE_PATH = os.path.join(SCRIPT_DIR, TASKS_FILE_NAME)




def calculate_next_run(cron_str):
    """Calculates the next run time from a CRON string."""
    if not cron_str:
        return ""
    try:
        now = datetime.now()
        iter = croniter(cron_str, now)
        return iter.get_next(datetime).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return "Invalid CRON"

def load_tasks():
    """Loads tasks from TASKS_FILE_PATH or initializes with defaults."""
    global tasks_data
    tasks_loaded_from_file = False
    if os.path.exists(TASKS_FILE_PATH):
        try:
            with open(TASKS_FILE_PATH, 'r') as f:
                if os.path.getsize(TASKS_FILE_PATH) == 0:
                    print(f"Warning: {TASKS_FILE_PATH} is empty. Loading default tasks.")
                else:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, list):
                        tasks_data = loaded_data
                        for task in tasks_data:
                            task.setdefault('id', str(uuid.uuid4()))
                            task.setdefault('name', 'Unnamed Task')
                            task.setdefault('bash_script_path', '')
                            task.setdefault('cron_expression', '')
                            task.setdefault('status_last_run', 'Not yet run') # Added default status
                            task['next_run_time'] = calculate_next_run(task.get('cron_expression', ''))
                        print(f"Tasks loaded successfully from {TASKS_FILE_PATH}")
                        tasks_loaded_from_file = True
                    else:
                        print(f"Warning: Data in {TASKS_FILE_PATH} is not a list. Loading default tasks.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {TASKS_FILE_PATH}. File might be corrupted. Loading default tasks.")
        except Exception as e:
            print(f"Error loading tasks from file {TASKS_FILE_PATH}: {e}. Loading default tasks.")

    if not tasks_loaded_from_file:
        if not os.path.exists(TASKS_FILE_PATH):
             print(f"{TASKS_FILE_PATH} not found. Loading default tasks.")
        
        default_base_id = datetime.now().strftime('%Y%m%d-%H%M%S')
        sample_tasks = [
            {'id': f"{default_base_id}_1", 'name': 'Daily Backup (Default)', 'bash_script_path': '/opt/scripts/backup.sh', 'cron_expression': '0 2 * * *', 'status_last_run': 'Not yet run'},
            {'id': f"{default_base_id}_2", 'name': 'Hourly Report (Default)', 'bash_script_path': '/usr/local/bin/generate_report.sh', 'cron_expression': '0 * * * *', 'status_last_run': 'Not yet run'},
            {'id': f"{default_base_id}_3", 'name': 'Manual Task (Default)', 'bash_script_path': '/home/user/manual_script.sh', 'cron_expression': '', 'status_last_run': 'Not yet run'}
        ]
        for task in sample_tasks:
            task['next_run_time'] = calculate_next_run(task['cron_expression'])
            # 'status_last_run' is already set in the dictionary definition
        tasks_data = sample_tasks
        print("Default tasks loaded.")
        save_tasks_to_file()

# --- Initial Data Loading -------------------------------------------------------------------------------
load_tasks()



##########################################################################################################
# --- Page Layouts ---
def create_main_page_layout():
    """Creates the layout for the main page (task list)."""
    global tasks_data

    header_row = html.Tr([
        html.Th("ID"), html.Th("Name"), html.Th("Bash Script Path"),
        html.Th("CRON Expression"), html.Th("Next Run Time"),
        html.Th("Status Last Run"), html.Th("Actions") # Added Status Last Run Header
    ])

    table_rows = []
    if tasks_data:
        for task in tasks_data:
            row = html.Tr([
                html.Td(task.get('id', 'N/A')),
                html.Td(task.get('name', 'N/A')),
                html.Td(task.get('bash_script_path', 'N/A')),
                html.Td(task.get('cron_expression', 'N/A')),
                html.Td(task.get('next_run_time', '')),
                html.Td(task.get('status_last_run', 'Not yet run')), # Added Status Last Run Data
                html.Td([
                    dbc.Button("Run", id={'type': 'run-task', 'index': task.get('id')}, size="sm", className="me-1", color="success", disabled=not task.get('id')),
                    dbc.Button("Edit", id={'type': 'edit-task', 'index': task.get('id')}, size="sm", className="me-1", color="warning", disabled=not task.get('id')),
                    dbc.Button("Copy", id={'type': 'copy-task', 'index': task.get('id')}, size="sm", className="me-1", color="info", disabled=not task.get('id')),
                    dbc.Button("Delete", id={'type': 'delete-task', 'index': task.get('id')}, size="sm", color="danger", disabled=not task.get('id')),
                ])
            ])
            table_rows.append(row)
    
    task_table = dbc.Table([html.Thead(header_row), html.Tbody(table_rows)],
                           bordered=True, striped=True, hover=True, responsive=True)

    return dbc.Container([
        dbc.Row(dbc.Col(dbc.Alert(id='main-page-alert', is_open=False, duration=15000), width=12), className="mt-3"),
        dbc.Row(dbc.Col(html.H1("Task List"), width=True), className="my-4"),
        dbc.Row(dbc.Col(dbc.Button("Add New Task", id="add-task-button-main", href="/manage-task", color="primary"), width="auto"), className="mb-3"),
        dbc.Row(dbc.Col(task_table if tasks_data else html.P("No tasks found. Add one or check 'tasks.json'!")))
    ], fluid=True)


def create_manage_task_layout(task_info=None, mode='add'):
    """Creates the layout for Add/Edit/Copy Task page."""
    # task_info could be the task to edit or task to copy
    # mode can be 'add', 'edit', 'copy'
    
    initial_name = task_info['name'] if task_info else ""
    initial_script_path = task_info['bash_script_path'] if task_info else ""
    initial_cron = task_info['cron_expression'] if task_info else ""
    editing_id = task_info['id'] if task_info and mode == 'edit' else None

    if mode == 'edit':
        page_title = "Edit Task"
    elif mode == 'copy':
        page_title = "Copy Task (will be saved as new)"
    else: # mode == 'add'
        page_title = "Add New Task"
        
    return dbc.Container([
        dcc.Store(id='edit-mode-store', data={'editing_id': editing_id, 'mode': mode}), 
        html.H1(page_title),
        dbc.Form([
            dbc.Row([
                dbc.Label("Name", html_for="task-name-input", width=2),
                dbc.Col(dbc.Input(type="text", id="task-name-input", value=initial_name, placeholder="Enter task name"), width=10),
            ], className="mb-3"),
            dbc.Row([
                dbc.Label("Bash Script Path", html_for="task-script-input", width=2),
                dbc.Col(dbc.Input(type="text", id="task-script-input", value=initial_script_path, placeholder="Enter absolute path to script"), width=10),
            ], className="mb-3"),
            dbc.Row([
                dbc.Label("CRON Expression", html_for="task-cron-input", width=2),
                dbc.Col(dbc.Input(type="text", id="task-cron-input", value=initial_cron, placeholder="e.g., 0 0 * * * (leave blank if none)"), width=10),
            ], className="mb-3"),
        ]),
        html.Div([
            dbc.Button("Save Task", id="save-task-button", color="success", className="me-2"),
            dbc.Button("Cancel", id="cancel-manage-task-button", href="/", color="secondary", outline=True),
        ], className="mt-4")
    ], className="mt-5")


# --- App Layout ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='alert-message-store', data={'message': '', 'color': 'info'}),
    html.Div(id='page-content')
])


##########################################################################################################
# --- Callbacks -----------------------------------------------------------------------------------------
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'), Input('url', 'search')]
)
def display_page(pathname, search_query):
    """Renders page content based on URL."""
    global tasks_data 
    if pathname == '/manage-task': # Unified page for add, edit, copy
        task_info = None
        mode = 'add' # Default mode
        if search_query: 
            params = dict(x.split('=') for x in search_query.strip('?').split('&') if '=' in x)
            edit_id = params.get('edit_id')
            copy_id = params.get('copy_id')

            if edit_id:
                task_info = next((task for task in tasks_data if task.get('id') == edit_id), None)
                mode = 'edit' if task_info else 'add' # Fallback to add if ID not found
            elif copy_id:
                task_info = next((task for task in tasks_data if task.get('id') == copy_id), None)
                mode = 'copy' if task_info else 'add' # Fallback to add if ID not found
        
        return create_manage_task_layout(task_info=task_info, mode=mode)
    return create_main_page_layout()

@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('alert-message-store', 'data', allow_duplicate=True)],
    [Input('save-task-button', 'n_clicks')],
    [State('task-name-input', 'value'),
     State('task-script-input', 'value'),
     State('task-cron-input', 'value'),
     State('edit-mode-store', 'data')], # Contains editing_id and mode
    prevent_initial_call=True
)
def save_task_callback(n_clicks, name, script_path, cron_expression, edit_mode_data):
    """Saves a new task or updates an existing task."""
    global tasks_data
    if not n_clicks:
        raise PreventUpdate

    if not name or not script_path: 
        return dash.no_update, {'message': 'Name and Script Path are required.', 'color': 'danger'}

    editing_id = edit_mode_data.get('editing_id') if edit_mode_data else None
    
    next_run = calculate_next_run(cron_expression)
    alert_message = ""

    if editing_id: # This is an update (edit) operation
        task_to_update = next((task for task in tasks_data if task.get('id') == editing_id), None)
        if task_to_update:
            task_to_update['name'] = name
            task_to_update['bash_script_path'] = script_path
            task_to_update['cron_expression'] = cron_expression if cron_expression else ""
            task_to_update['next_run_time'] = next_run
            # status_last_run is not modified here, only on actual run
            alert_message = f"Task '{name}' (ID: {editing_id}) updated successfully!"
            task_add_cron(task_to_update)
        else: # Should not happen if flow is correct
            return dash.no_update, {'message': f"Error: Task with ID {editing_id} not found for update.", 'color': 'danger'}
    else: # This is a new task (either fresh add or from copy)
        base_id = datetime.now().strftime('%Y%m%d-%H%M%S')
        new_task_id = base_id
        counter = 1
        while any(task.get('id') == new_task_id for task in tasks_data):
            new_task_id = f"{base_id}_{counter}"
            counter += 1
            if counter > 100: 
                new_task_id = f"{base_id}_{str(uuid.uuid4())[:4]}"
                break
            
        new_task = {
            'id': new_task_id, 'name': name, 'bash_script_path': script_path,
            'cron_expression': cron_expression if cron_expression else "", 
            'next_run_time': next_run,
            'status_last_run': 'Not yet run' # Initialize for new task
        }
        tasks_data.append(new_task)
        alert_message = f"Task '{name}' (ID: {new_task_id}) saved successfully!"
        task_add_cron(new_task)

        
    save_tasks_to_file() 
    return '/', {'message': alert_message, 'color': 'success'}


@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('url', 'search', allow_duplicate=True),
     Output('alert-message-store', 'data', allow_duplicate=True)],
    [Input({'type': 'run-task', 'index': ALL}, 'n_clicks'),
     Input({'type': 'edit-task', 'index': ALL}, 'n_clicks'), 
     Input({'type': 'copy-task', 'index': ALL}, 'n_clicks'),
     Input({'type': 'delete-task', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def handle_task_actions_callback(run_n_clicks, edit_n_clicks, copy_n_clicks, delete_n_clicks):
    """Handles Run, Edit, Copy, Delete actions for tasks."""
    global tasks_data
    ctx = callback_context
    if not ctx.triggered or not ctx.triggered_id:
        raise PreventUpdate

    # Ensure triggered_id is a dictionary (pattern-matching callbacks)
    triggered_prop_id = ctx.triggered[0]['prop_id']
    # prop_id is like '{"index":"task_id_1","type":"run-task"}.n_clicks'
    # We need to parse the JSON part to get the 'index' and 'type'
    try:
        # Extract the JSON string part: '{"index":"task_id_1","type":"run-task"}'
        json_str = triggered_prop_id.split('.')[0]
        button_id_dict = json.loads(json_str)
    except Exception as e:
        print(f"Error parsing button_id_dict: {e}, from: {triggered_prop_id}")
        raise PreventUpdate

    action_type = button_id_dict.get('type')
    task_id = button_id_dict.get('index')
 
    task = next((t for t in tasks_data if t.get('id') == task_id), None)
    
    if not task: 
        return dash.no_update, dash.no_update, {'message': 'Task not found or ID mismatch.', 'color': 'danger'}

    alert_data = {'message': '', 'color': 'info'}

    if action_type == 'run-task':
        alert_data = run_task(task) # run_task will now update task's status_last_run and save
        return '/', '', alert_data # Redirect to main page to refresh and show new status
    
    elif action_type == 'edit-task':
        return '/manage-task', f'?edit_id={task_id}', {'message': f"Editing task: {task.get('name')}", 'color': 'info'}

    elif action_type == 'copy-task':
        return '/manage-task', f'?copy_id={task_id}', {'message': f"Pre-filled form to copy task: {task.get('name')}. Save to create a new task.", 'color': 'info'}

    elif action_type == 'delete-task':
        task_name_deleted = task.get('name', 'Unknown task')
        # Also remove from crontab if it exists
        task_remove_cron(task, show=0) # show=0 to make it less verbose if not needed
        tasks_data = [t for t in tasks_data if t.get('id') != task_id]
        save_tasks_to_file() 
        alert_data = {'message': f"Task '{task_name_deleted}' deleted.", 'color': 'warning'}
        return '/', '', alert_data # Redirect to main page to refresh

    raise PreventUpdate


@app.callback(
    [Output('main-page-alert', 'children'),
     Output('main-page-alert', 'is_open'),
     Output('main-page-alert', 'color')],
    [Input('alert-message-store', 'data')]
)
def show_main_page_alert(alert_data):
    """Displays alerts on the main page based on data from alert-message-store."""
    if alert_data and alert_data.get('message'):
        return alert_data['message'], True, alert_data['color']
    return "", False, "info"


#######################################################################################
# --- Helper Functions ---------------------------------------------------------------

def save_tasks_to_file():
    """Saves the current tasks_data to TASKS_FILE_PATH."""
    global tasks_data
    try:
        # Ensure all tasks have the new field before saving, just in case
        for task_entry in tasks_data:
            task_entry.setdefault('status_last_run', 'Not yet run')
        with open(TASKS_FILE_PATH, 'w') as f:
            json.dump(tasks_data, f, indent=4)
        print(f"Tasks saved successfully to {TASKS_FILE_PATH}")
    except Exception as e:
        print(f"Error saving tasks to {TASKS_FILE_PATH}: {e}")


#######################################################################################
def task_add_cron(task):
    from crontab import CronTab

    cron = CronTab(user=True)
    cmd = task.get('bash_script_path', "")
    taskid = task.get('id', "-1")
    schedule = task.get('cron_expression', "")

    # Remove existing job with the same comment before adding/updating
    # This handles updates to schedule or command for an existing task ID
    # Iterate over jobs and remove if comment matches 'cron_ui' + taskid
    for job in cron.find_comment('cron_ui' + taskid):
        cron.remove(job)
    
    if not schedule: # If cron_expression is empty, don't add to crontab
        print(f"Task '{task.get('name')}' (ID: {taskid}) has no CRON expression. Not adding to system crontab.")
        cron.write() # Save changes if any (like removals)
        return

    if len(cmd) < 1: # Basic check for command
        print(f"Invalid command for task ID {taskid}. Not adding to system crontab.")
        cron.write()
        return

    try:
        if not croniter.is_valid(schedule):
            print(f"Invalid CRON expression: '{schedule}' for task ID {taskid}. Not adding to system crontab.")
            cron.write()
            return
    except Exception as e:
        print(f"Error validating CRON expression '{schedule}' for task ID {taskid}: {e}. Not adding to system crontab.")
        cron.write()
        return

    job = cron.new(command=cmd, comment='cron_ui' + taskid)
    job.setall(schedule)
    cron.write() # Use write_safe to avoid issues with temp files
    print(f"Cron job for task ID {taskid} set/updated: {job}")



def task_remove_cron(task, show=1):
    from crontab import CronTab
    cron = CronTab(user=True)
    taskid = task.get('id')
    jobs_removed = 0
    for job in cron.find_comment('cron_ui' + taskid):
        cron.remove(job)
        jobs_removed += 1
        if show:
            print(f"Removed cron job for task ID {taskid}: {job}")
    
    if jobs_removed > 0:
        cron.write()
    elif show:
        print(f"No cron job found with comment 'cron_ui{taskid}' to remove.")



#######################################################################################
def run_task(task):
   """Runs the task script and updates its status."""
   script_path = task.get('bash_script_path')
   task_name = task.get('name', 'Unnamed Task')
   
   print(f"Attempting to run task: {task_name}")
   print(f"Script: {script_path}")

   run_message = ""
   run_color = "info"

   try:
       # run_shell_script now returns a more detailed message
       execution_summary = run_shell_script(script_path) 
       run_message = f"Task '{task_name}': {execution_summary}"
       task['status_last_run'] = f"{execution_summary} (Initiated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
       run_color = "success" if "Started" in execution_summary else "warning" # Basic check
   except FileNotFoundError:
       run_message = f"Error running task '{task_name}': Script '{script_path}' not found."
       task['status_last_run'] = f"Script not found (At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
       run_color = "danger"
   except PermissionError:
       run_message = f"Error running task '{task_name}': Permission denied for script '{script_path}'. Make sure it's executable."
       task['status_last_run'] = f"Permission denied (At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
       run_color = "danger"
   except Exception as e:
       run_message = f"An unexpected error occurred while trying to run task '{task_name}': {e}"
       task['status_last_run'] = f"Failed to start: {e} (At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
       run_color = "danger"
       print(f"Exception in run_task: {e}")

   save_tasks_to_file() # Persist the updated status_last_run

   alert_dict = {'message': run_message, 'color': run_color}
   return alert_dict


def run_shell_script(script_path):
    """
    Run a shell script after loading .zshrc.
    Args:
        script_path (str): Path to the shell script to execute.
    Returns:
        str: A message indicating the outcome of the script initiation.
    Raises:
        FileNotFoundError: If the script_path does not exist.
        PermissionError: If the script is not executable.
    """
    import subprocess
    import os    
    
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    if not os.access(script_path, os.X_OK):
        try:
            os.chmod(script_path, 0o755) # Try to make it executable
            print(f"Made script executable: {script_path}")
        except Exception as e:
            print(f"Could not make script executable {script_path}: {e}")
            raise PermissionError(f"Script not executable and could not be made executable: {script_path}")

    cmd = f"{script_path}"
    
    try:
        # Use system default shell, fallback to /binz/sh
        default_shell = os.environ.get('SHELL', '/bin/zsh')
        process = subprocess.Popen(
            cmd,
            shell=True,
            executable=default_shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            close_fds=True # Recommended for security and resource management
        )
        
        # Brief wait to allow process to start and potentially get initial info
        # Note: This does NOT wait for the script to complete.
        time.sleep(0.5) 

        pid = process.pid
        # Check if process is still running; it might finish very quickly
        try:
            # psutil would be more robust here if available
            # For now, a simple check or rely on Popen not erroring immediately
            os.kill(pid, 0) # Check if process exists
            is_running = True
        except OSError:
            is_running = False
        
        if is_running:
            # Attempt to get usage info; might fail if script is too short-lived
            # or if ps command structure isn't quite right for all systems/outputs
            try:
                info = os_get_process_usage_subprocess(pid)
                if not info or f"{pid}" not in info: # If ps didn't find the pid
                    info = "Process completed or info unavailable."
            except Exception as e_info:
                info = f"Could not get process info: {e_info}"
            return f"Started '{os.path.basename(script_path)}' (PID: {pid}). Usage: {info.strip()}"
        else:
            # If not running, try to get return code
            # Note: communicate() will wait for completion if called here
            stdout, stderr = process.communicate(timeout=2) # Small timeout
            if process.returncode == 0:
                return f"Script '{os.path.basename(script_path)}' (PID: {pid}) likely completed quickly. Output: {stdout[:100]}"
            else:
                return f"Script '{os.path.basename(script_path)}' (PID: {pid}) may have failed quickly. Error: {stderr[:100]}"


    except Exception as e:
        return f"Failed to start script '{os.path.basename(script_path)}': {str(e)}"


def os_get_process_info(pid):
    """
    Get detailed information about a specific process ID
    """
    import subprocess
    cmd = f"ps -fp {pid}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        return result.stdout
    except Exception as e:
        return f"Failed to get process info for PID {pid}: {e}"


def os_get_process_usage_subprocess(pid):
    """
    Get RAM and CPU usage using subprocess commands
    """
    import subprocess    
    cmd = f"ps -p {pid} -o pid,pcpu,pmem,rss,cmd --no-headers"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        if result.stdout.strip():
            return result.stdout.strip()
        return "Process info not found (possibly completed)."
    except Exception as e:
        return f"Failed to get process usage for PID {pid}: {e}"


if __name__ == '__main__':
    app.run_server(debug=True,port=9721)
