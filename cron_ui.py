"""


"""
import uuid, os, traceback, time, json
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, ALL, MATCH, callback_context
from dash.exceptions import PreventUpdate
from croniter import croniter
from crontab import CronTab # Ensure this is imported at the top level





#################################################################################
# --- Global Variables & Constants ----------------------------------------------
tasks_data = []
TASKS_FILE_NAME = "ztmp/tasks.json"
# Determine the directory of the currently running script to locate tasks.json
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE_PATH = os.path.join(SCRIPT_DIR, TASKS_FILE_NAME)
LOG_DIR_NAME = "ztmp/log" # Added for log directory
LOG_DIR_PATH = os.path.join(SCRIPT_DIR, LOG_DIR_NAME) # Added for log directory


#################################################################################
# --- App Initialization and Configuration --------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA], suppress_callback_exceptions=True)
app.title = "Task List"






#################################################################################
def cron_calculate_next_run(cron_str):
    """Calculates the next run time from a CRON string."""
    if not cron_str:
        return ""
    try:
        now = datetime.now()
        iter = croniter(cron_str, now)
        return iter.get_next(datetime).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return "Invalid CRON"


#################################################################################
def cron_calculate_next_run(cron_str):
    """Calculates the next run time from a CRON string."""
    if not cron_str:
        return ""
    try:
        now = datetime.now()
        iter = croniter(cron_str, now)
        return iter.get_next(datetime).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return "Invalid CRON"

def tasks_load():
    """Loads tasks from TASKS_FILE_PATH or initializes with defaults."""
    global tasks_data
    tasks_loaded_from_file = False
    try:
        with open(TASKS_FILE_PATH, 'r') as f:
                loaded_data = json.load(f)
        tasks_data = loaded_data
        for task in tasks_data:
            task.setdefault('id', str(uuid.uuid4()))
            task.setdefault('name', 'Unnamed Task')
            task.setdefault('bash_script_path', '')
            task.setdefault('cron_expression', '')
            task.setdefault('status_last_run', 'Not yet run') # Added default status
            task['next_run_time'] = cron_calculate_next_run(task.get('cron_expression', ''))

        print(f"Tasks loaded successfully from {TASKS_FILE_PATH}")
        tasks_loaded_from_file = True

    except Exception as e:
        print(f"Error loading tasks from file {TASKS_FILE_PATH}: {e}. Loading default tasks.")


    if not tasks_loaded_from_file:
        print(f"{TASKS_FILE_PATH} not found. Loading default tasks.")
        default_base_id = datetime.now().strftime('%Y%m%d-%H%M%S')
        sample_tasks = [
            {'id': f"{default_base_id}_1", 'name': 'Daily Backup (Default)', 'bash_script_path': '/opt/scripts/backup.sh', 'cron_expression': '0 2 * * *', 'status_last_run': 'Not yet run'},
            {'id': f"{default_base_id}_2", 'name': 'Hourly Report (Default)', 'bash_script_path': '/usr/local/bin/generate_report.sh', 'cron_expression': '0 * * * *', 'status_last_run': 'Not yet run'},
            {'id': f"{default_base_id}_3", 'name': 'Manual Task (Default)', 'bash_script_path': '/home/user/manual_script.sh', 'cron_expression': '', 'status_last_run': 'Not yet run'}
        ]
        for task in sample_tasks:
            task['next_run_time'] = cron_calculate_next_run(task['cron_expression'])
            # 'status_last_run' is already set in the dictionary definition
        tasks_data = sample_tasks
        print("Default tasks loaded.")
        tasks_save_to_file()

# --- Initial Data Loading -------------------------------------------------------------------------------
tasks_load()





##########################################################################################################
# --- Page Layouts ---------------------------------------------------------------------------------------

# In your layout where you define the task editing form
# This global definition is noted, but instantiation happens in layout_create_manage_task
script_content_textarea = dbc.Textarea(
    id='task-script-content',
    placeholder="Script content...",
    style={"height": "300px"},
)



def layout_create_main_page():
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

    # --- ADDITION: Fetch crontab content ---
    crontab_content_str = crontab_get_content()
    if not crontab_content_str.strip():
        crontab_content_str = "# No crontab entries found for the current user or crontab is empty."
    # --- END ADDITION ---

    return dbc.Container([
        dbc.Row(dbc.Col(dbc.Alert(id='main-page-alert', is_open=False, duration=15000), width=12), className="mt-3"),
        dbc.Row(dbc.Col(html.H5("Task List"), width=True), className="my-4"),
        dbc.Row(dbc.Col(dbc.Button("Add New Task", id="add-task-button-main", href="/manage-task", color="primary"), width="auto"), className="mb-3"),
        dbc.Row(dbc.Col(task_table if tasks_data else html.P("No tasks found. Add one or check 'tasks.json'!"))),
        
        # --- ADDITION: Display Crontab Content ---
        html.Hr(className="my-4"), # Visual separator
        dbc.Row(
            dbc.Col([
                html.H5("Current User Crontab"),
                html.Pre(
                    children=crontab_content_str,
                    id='crontab-display',
                    style={
                        'border': '1px solid #ddd',
                        'padding': '10px',
                        'maxHeight': '300px',
                        'overflowY': 'auto',
                        'whiteSpace': 'pre-wrap', # Ensures lines wrap and are treated as preformatted
                        'wordBreak': 'break-all', # Breaks long lines if necessary
                        'background': '#f8f9fa' # Light background for readability
                    }
                )
            ]),
            className="mb-4" # Add some margin at the bottom
        )
        # --- END ADDITION ---
        ,
        # --- ADDITION: Display Log Files ---
        html.Hr(className="my-4"), # Visual separator
        dbc.Row(
            dbc.Col([
                html.H5("Log Files (ztmp/log)"),
                html.Div(list_log_files(), id='log-files-display') # Call the new function here
            ]),
            className="mb-4"
        )
        # --- END ADDITION ---
    ], fluid=True)


def layout_create_manage_task(task_info=None, mode='add'):
    """Creates the layout for Add/Edit/Copy Task page."""
    initial_name = task_info['name'] if task_info else ""
    initial_script_path = task_info['bash_script_path'] if task_info else ""
    initial_cron = task_info['cron_expression'] if task_info else ""
    editing_id = task_info['id'] if task_info and mode == 'edit' else None

    initial_script_content = ""
    if initial_script_path: 
        initial_script_content = script_read_content(initial_script_path)

    if mode == 'edit':
        page_title = "Edit Task"
    elif mode == 'copy':
        page_title = "Copy Task (will be saved as new)"
    else: 
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
            dbc.Row([
                dbc.Label("Script Content", html_for="task-script-content", width=2), 
                dbc.Col([ 
                    dbc.Textarea(
                        id='task-script-content',
                        value=initial_script_content, 
                        placeholder="Enter or edit script content here. Content will be loaded if 'Bash Script Path' is valid and file exists. Changes will be saved to the path.",
                        style={"height": "300px"},
                    )
                ], width=10) 
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
], style={'fontSize': '11px'}) # You can adjust    





##########################################################################################################
# --- Callbacks -----------------------------------------------------------------------------------------
@app.callback(
    Output('task-script-content', 'value'),
    [Input('task-script-input', 'value')],
    prevent_initial_call=True
)
def callback_load_script_content(script_path): # Renamed to avoid conflict with function name
    if not script_path:
        return ""
    return script_read_content(script_path)


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname'), Input('url', 'search')]
)
def callback_display_page(pathname, search_query):
    """Renders page content based on URL."""
    global tasks_data 
    if pathname == '/manage-task': 
        task_info = None
        mode = 'add' 
        if search_query: 
            params = dict(x.split('=') for x in search_query.strip('?').split('&') if '=' in x)
            edit_id = params.get('edit_id')
            copy_id = params.get('copy_id')

            if edit_id:
                task_info = next((task for task in tasks_data if task.get('id') == edit_id), None)
                mode = 'edit' if task_info else 'add' 
            elif copy_id:
                task_info = next((task for task in tasks_data if task.get('id') == copy_id), None)
                mode = 'copy' if task_info else 'add' 
        
        return layout_create_manage_task(task_info=task_info, mode=mode)
    return layout_create_main_page()


@app.callback(
    [Output('url', 'pathname', allow_duplicate=True),
     Output('alert-message-store', 'data', allow_duplicate=True)],
    [Input('save-task-button', 'n_clicks')],
    [State('task-name-input', 'value'),
     State('task-script-input', 'value'),
     State('task-script-content', 'value'), 
     State('task-cron-input', 'value'),
     State('edit-mode-store', 'data')], 
    prevent_initial_call=True
)
def callback_save_task(n_clicks, name, script_path, script_content, cron_expression, edit_mode_data):
    global tasks_data
    if not n_clicks:
        raise PreventUpdate

    if not name or not script_path: 
        return dash.no_update, {'message': 'Name and Script Path are required.', 'color': 'danger'}

    editing_id = edit_mode_data.get('editing_id') if edit_mode_data else None
    
    next_run = cron_calculate_next_run(cron_expression)
    alert_message = ""

    if editing_id: 
        task_to_update = next((task for task in tasks_data if task.get('id') == editing_id), None)
        if task_to_update:
            task_to_update['name'] = name
            task_to_update['bash_script_path'] = script_path
            task_to_update['cron_expression'] = cron_expression if cron_expression else ""
            task_to_update['next_run_time'] = next_run
            alert_message = f"Task '{name}' (ID: {editing_id}) updated successfully!"
            task_add_cron(task_to_update)
        else: 
            return dash.no_update, {'message': f"Error: Task with ID {editing_id} not found for update.", 'color': 'danger'}
    else: 
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
            'status_last_run': 'Not yet run' 
        }
        tasks_data.append(new_task)
        alert_message = f"Task '{name}' (ID: {new_task_id}) saved successfully!"
        task_add_cron(new_task)

    if script_content is not None: 
        save_result = script_save_content(script_path, script_content)
        if not save_result:
            return dash.no_update, {'message': f'Error saving script to {script_path}. Task not saved/updated.', 'color': 'danger'}
        
    tasks_save_to_file() 
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
def callback_task_handle_actions(run_n_clicks, edit_n_clicks, copy_n_clicks, delete_n_clicks):
    global tasks_data
    ctx = callback_context
    if not ctx.triggered or not ctx.triggered_id:
        raise PreventUpdate

    triggered_prop_id = ctx.triggered[0]['prop_id']
    try:
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
        alert_data = tasks_run(task) 
        return '/', '', alert_data 
    
    elif action_type == 'edit-task':
        return '/manage-task', f'?edit_id={task_id}', {'message': f"Editing task: {task.get('name')}", 'color': 'info'}

    elif action_type == 'copy-task':
        return '/manage-task', f'?copy_id={task_id}', {'message': f"Pre-filled form to copy task: {task.get('name')}. Save to create a new task.", 'color': 'info'}

    elif action_type == 'delete-task':
        task_name_deleted = task.get('name', 'Unknown task')
        task_remove_cron(task, show=0) 
        tasks_data = [t for t in tasks_data if t.get('id') != task_id]
        tasks_save_to_file() 
        alert_data = {'message': f"Task '{task_name_deleted}' deleted.", 'color': 'warning'}
        return '/', '', alert_data 

    raise PreventUpdate


@app.callback(
    [Output('main-page-alert', 'children'),
     Output('main-page-alert', 'is_open'),
     Output('main-page-alert', 'color')],
    [Input('alert-message-store', 'data')]
)
def callback_show_main_page_alert(alert_data):
    """
    Displays an alert on the main page by updating the alert's children, 
    open state, and color based on the data from 'alert-message-store'.

    Parameters:
    alert_data (dict): A dictionary containing the alert message and color.
    """
    if alert_data and alert_data.get('message'):
        return alert_data['message'], True, alert_data['color']
    return "", False, "info"



#######################################################################################
# --- Helper Functions ---------------------------------------------------------------

def save_tasks_to_file():
    global tasks_data
    try:
        for task_entry in tasks_data:
            task_entry.setdefault('status_last_run', 'Not yet run')
        with open(TASKS_FILE_PATH, 'w') as f:
            json.dump(tasks_data, f, indent=4)
        print(f"Tasks saved successfully to {TASKS_FILE_PATH}")
    except Exception as e:
        print(f"Error saving tasks to {TASKS_FILE_PATH}: {e}")









#######################################################################################
# --- Task Execution Functions -------------------------------------------------------
def tasks_run(task):
   script_path = task.get('bash_script_path')
   task_name   = task.get('name', 'Unnamed Task')
   
   print(f"Attempting to run task: {task_name}")
   print(f"Script: {script_path}")

   run_message = ""
   run_color   = "info"

   try:
       execution_summary = run_shell_script(script_path, task) 
       run_message = f"Task '{task_name}': {execution_summary}"
       task['status_last_run'] = f"{execution_summary} (Initiated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
       run_color = "success" if "Started" in execution_summary or "completed quickly" in execution_summary else "warning" 

   except Exception as e:
       run_message = f"An unexpected error occurred while trying to run task '{task_name}': {e}"
       task['status_last_run'] = f"Failed to start: {e} (At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
       run_color = "danger"
       print(f"Exception in tasks_run: {e}")
       print(traceback.format_exc())

   tasks_save_to_file() 

   alert_dict = {'message': run_message, 'color': run_color}
   return alert_dict



def tasks_save_to_file():
    global tasks_data
    try:
        for task_entry in tasks_data:
            task_entry.setdefault('status_last_run', 'Not yet run')
        with open(TASKS_FILE_PATH, 'w') as f:
            json.dump(tasks_data, f, indent=4)
        print(f"Tasks saved successfully to {TASKS_FILE_PATH}")
    except Exception as e:
        print(f"Error saving tasks to {TASKS_FILE_PATH}: {e}")



def date_get_ymdhms(dt=None):
    from datetime import datetime
    if dt is None:
        dt = datetime.now()
    
    year = str(dt.year)
    month = f"{dt.month:02d}"
    day = f"{dt.day:02d}"
    hour = f"{dt.hour:02d}"
    minute = f"{dt.minute:02d}"
    second = f"{dt.second:02d}"
    
    return year, month, day, hour, minute, second


def run_shell_script(script_path, task):
    import subprocess
    import os    
        
    os.chmod(script_path, 0o755) 

    fname = os.path.basename(script_path)
    fname = fname.split('.')[0]

    print(f"Made script executable: {script_path}")

    task_str = str(task)

    dircurr = os.path.abspath(os.getcwd())
    print(dircurr)
    year, month, day, hour, minute, second = date_get_ymdhms()
    dirlog = f"{dircurr}/ztmp/log/year={year}/month={month}/day={day}/hour={hour}"
    logfile= f"{dirlog}/task_{year}{month}{day}_{hour}{minute}{second}_{fname}.log"

    os.makedirs(f"{dirlog}", exist_ok=True)
    os.system(f"echo '## date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}' > {logfile}")
    os.system(f"echo '## script: {script_path}' >> {logfile}")
    os.system(f"echo '## task: {task_str}' >> {logfile}")
    os.system(f"echo '\n\n\n' >> {logfile}")

    cmd = f"cd '{dircurr}' 2>&1 | tee -a  '{logfile}'  && echo $(pwd) 2>&1 | tee -a  '{logfile}'  &&  {script_path} 2>&1 | tee -a  '{logfile}' "
    print(f"Running: {cmd}")


    try:
        default_shell = os.environ.get('SHELL', '/bin/zsh')
        print(f"Using shell: {default_shell}")
        process = subprocess.Popen(
            cmd,
            shell=True,
            executable=default_shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        time.sleep(0.5) 
        pid = process.pid


        try:
            info = os_get_process_usage_subprocess(pid)
        except Exception as e_info:
            info = f"Could not get process info: {e_info}"

        msg = f"Started '{script_path}' (PID: {pid}). Usage: {info.strip()}"
        return msg

    except Exception as e:
        return f"Failed to start script '{script_path}': {str(e)}"


def os_get_process_info(pid):
    import subprocess
    cmd = f"ps -fp {pid}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        return result.stdout
    except Exception as e:
        return f"Failed to get process info for PID {pid}: {e}"


def os_get_process_usage_subprocess(pid):
    import subprocess    
    cmd = f"ps -p {pid} -o pid,pcpu,pmem,rss,cmd"
    print(cmd)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        return result.stdout

    except Exception as e:
        return f"Failed to get process usage for PID {pid}: {e}"



########################################################################################
def task_add_cron(task):
    # from crontab import CronTab # Already imported globally

    cron = CronTab(user=True)
    cmd = task.get('bash_script_path', "")
    taskid = task.get('id', "-1")
    schedule = task.get('cron_expression', "")

    for job in cron.find_comment('cron_ui' + taskid):
        cron.remove(job)
    
    if not schedule: 
        print(f"Task '{task.get('name')}' (ID: {taskid}) has no CRON expression. Not adding to system crontab.")
        cron.write() 
        return

    if len(cmd) < 1: 
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
    cron.write() 
    print(f"Cron job for task ID {taskid} set/updated: {job}")



def task_remove_cron(task, show=1):
    # from crontab import CronTab # Already imported globally
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



def crontab_get_content():
    """Fetches the current user's crontab content as a string."""
    try:
        user_cron = CronTab(user=True)
        return user_cron.render()
    except Exception as e:
        print(f"Error reading user crontab: {e}")
        return f"# Could not retrieve crontab.\n# Error: {str(e)}"



#######################################################################################
def script_read_content(file_path):
    """Reads content from a script file path."""

    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading script file {file_path}: {e}")
        return ""



def script_save_content(file_path, content):
    """Saves content to a script file path."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error saving script file {file_path}: {e}")
        return False


def list_log_files() -> list:
    """Lists files in the log directory and returns them as html.A components."""
    log_files_components = []
    log_dir_abs = LOG_DIR_PATH

    if not os.path.exists(log_dir_abs):
        return [html.P(f"Log directory not found: {log_dir_abs}")]
    if not os.path.isdir(log_dir_abs):
        return [html.P(f"Log path is not a directory: {log_dir_abs}")]

    try:
        for root, _, files in os.walk(log_dir_abs):
            for file_name in files:
                # Construct a relative path from the SCRIPT_DIR for the link
                # This makes the link work if the app is served from the script's directory
                # or if a route is set up to serve files from ztmp/log
                # For local file URLs, we need to be careful with how they are generated.
                # A simple relative path might not work directly in all browsers for file:// protocol.
                # However, for a web app, these would typically be served via HTTP.
                # Assuming a local context for now, or that these will be served.
                relative_log_path = os.path.join(LOG_DIR_NAME, os.path.relpath(os.path.join(root, file_name), log_dir_abs))
                # Ensure forward slashes for URL compatibility, even on Windows for the href
                href_path = relative_log_path.replace(os.sep, '/')

                fp = os.path.abspath(os.path.join(SCRIPT_DIR, href_path)) 
                log_files_components.append(html.Li(html.A(href_path, href=f"file://{fp}", )))

        if not log_files_components:
            return [html.P("No .log files found in the log directory.")]

    except Exception as e:
        return [html.P(f"Error listing log files: {str(e)}")]
    return [html.Ul(log_files_components)]






#######################################################################################
if __name__ == '__main__':
    TASKS_FILE_NAME = "ztmp/tasks.json"
    # Determine the directory of the currently running script to locate tasks.json
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TASKS_FILE_PATH = os.path.join(SCRIPT_DIR, TASKS_FILE_NAME)

    app.run_server(debug=True,port=9721)

