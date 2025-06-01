"""
   
  cd cron_ui
  python3 cron_ui.py


"""
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
            {'id': f"{default_base_id}_1", 'name': 'Daily Backup (Default)', 'bash_script_path': '/opt/scripts/backup.sh', 'cron_expression': '0 2 * * *'},
            {'id': f"{default_base_id}_2", 'name': 'Hourly Report (Default)', 'bash_script_path': '/usr/local/bin/generate_report.sh', 'cron_expression': '0 * * * *'},
            {'id': f"{default_base_id}_3", 'name': 'Manual Task (Default)', 'bash_script_path': '/home/user/manual_script.sh', 'cron_expression': ''}
        ]
        for task in sample_tasks:
            task['next_run_time'] = calculate_next_run(task['cron_expression'])
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
        html.Th("CRON Expression"), html.Th("Next Run Time"), html.Th("Actions")
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
            'next_run_time': next_run
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
     Input({'type': 'edit-task', 'index': ALL}, 'n_clicks'), # Added Edit
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

    button_id_dict = ctx.triggered_id
    action_type = button_id_dict.get('type')
    task_id = button_id_dict.get('index')
 
    task = next((t for t in tasks_data if t.get('id') == task_id), None)
    
    if not task: 
        return dash.no_update, dash.no_update, {'message': 'Task not found or ID mismatch.', 'color': 'danger'}

    alert_data = {'message': '', 'color': 'info'}

    if action_type == 'run-task':
        alert_data = run_task(task)
        return dash.no_update, dash.no_update, alert_data
    
    elif action_type == 'edit-task':
        # Redirect to the manage task page in 'edit' mode
        return '/manage-task', f'?edit_id={task_id}', {'message': f"Editing task: {task.get('name')}", 'color': 'info'}

    elif action_type == 'copy-task':
        # Redirect to the manage task page in 'copy' mode
        return '/manage-task', f'?copy_id={task_id}', {'message': f"Pre-filled form to copy task: {task.get('name')}. Save to create a new task.", 'color': 'info'}

    elif action_type == 'delete-task':
        task_name_deleted = task.get('name', 'Unknown task')
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
        with open(TASKS_FILE_PATH, 'w') as f:
            json.dump(tasks_data, f, indent=4)
        print(f"Tasks saved successfully to {TASKS_FILE_PATH}")
    except Exception as e:
        print(f"Error saving tasks to {TASKS_FILE_PATH}: {e}")




#######################################################################################
def task_add_cron(task):
    from crontab import CronTab

    # Create a CronTab instance for the current user
    cron = CronTab(user=True)

    cmd      = task.get('bash_script_path', "")
    taskid   = task.get('id', "-1")
    schedule = task.get('cron_expression', "")

    if len(schedule) < 2:
        log("Invalid CRON expression:", schedule)
        return

    if len(cmd) < 4:
        log("Invalid cmd:", cmd)
        return

    ### IF Same exist    
    task_remove_cron(task, show=1)


    # Create a new cron job with a full cron expression
    job = cron.new(command=cmd, comment='cron_ui' + taskid )

    # Set the schedule using a full cron expression (2:30 AM every day)
    job.setall(schedule)

    # Write the job to the crontab
    cron.write()
    
    # Iterate through all jobs and print them
    for job in cron:
        print(job)



def task_remove_cron(task, show=1):
    from crontab import CronTab

    # Create a CronTab instance for the current user
    cron = CronTab(user=True)

    cmd = task.get('bash_script_path')
    taskid = task.get('id')

    # Iterate over all jobs and remove the one with the specific comment
    for job in cron:
        try: 
            if job.comment == 'cron_ui' + taskid :
                cron.remove(job)
                print(cmd)
        except Exception as e:
            print(f"Error removing job: {e}")        

    # Write the updated crontab
    cron.write()
    

    # Iterate through all jobs and print them
    for job in cron:
        print(job)





#######################################################################################
def run_task(task):
   print(f"Simulating run for task: {task.get('name')} ")
   print(f"Script: {task.get('bash_script_path')}")
   ddict = {'message': f"Simulated run for task: {task.get('name')}", 'color': 'info'}

   script_path = task.get('bash_script_path')

   msg = run_shell_script(script_path)

   ddict = {'message': msg, 'color': 'info'}
   return ddict


def run_shell_script(script_path):
    """
    Run a shell script after loading .zshrc
    Args:
        script_path (str): Path to the shell script to execute
    """
    import subprocess
    import os    
    # Make sure the script path exists and is executable
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    # Make the script executable if it's not already
    if not os.access(script_path, os.X_OK):
        os.chmod(script_path, 0o755)
    
    # Command to source .zshrc and then run the script
    cmd = f"source ~/.zshrc && {script_path}"
    
    # Run the command in a zsh shell
    process = subprocess.Popen(
        cmd,
        shell=True,
        executable="/bin/zsh",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(1)
    
    pid = process.pid
    info = os_get_process_usage_subprocess(pid)
    
    msg=f"Started {script_path} , PID: {process.pid}.\n Info: {info}"
    
    return msg


def os_get_process_info(pid):
    """
    Get detailed information about a specific process ID
    """
    import subprocess
    cmd = f"ps -fp {pid}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


def os_get_process_usage_subprocess(pid):
    """
    Get RAM and CPU usage using subprocess commands
    """
    import subprocess    
    cmd = f"ps -p {pid} -o pid,pcpu,pmem,rss,cmd"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


if __name__ == '__main__':
    app.run_server(debug=True,port=9721)


