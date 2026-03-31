from datetime import datetime, date

# Hardkodovani taskovi
tasks = [
        {
            "TaskID": 101,
            "TaskName": "Prepare Monthly Report",
            "TaskCategory": "Reporting",
            "CreatedDate": "2025-01-05",
            "EndDate": "2025-01-12",
            "ActivationDate":"2025-01-12",
            "AssignedTo": "Marko Sovrovic"
        },
        {
            "TaskID": 102,
            "TaskName": "Security Patch Deployment",
            "TaskCategory": "Security Review",
            "CreatedDate": "2025-01-03",
            "EndDate": "2025-01-10",
            "ActivationDate":"2025-01-12",
            "AssignedTo": "Branislav Tomic"
        },
        {
            "TaskID": 103,
            "TaskName": "Onboarding New Employee",
            "TaskCategory": "People Management",
            "CreatedDate": "2025-01-07",            
            "EndDate": "2025-01-20",
            "ActivationDate":"2025-01-12",
            "AssignedTo": "Dejan Vasilic"
        },
         {
            "TaskID": 103,
            "TaskName": "Onboarding New Employee",
            "TaskCategory": "People Management",
            "CreatedDate": "2025-01-07",            
            "EndDate": "2025-01-20",
            "ActivationDate":"NA",
            "AssignedTo": "NA"
        }
    ]

# Funkcija za dobijanje taska po ID
def get_task(task_id):
    return next((t for t in tasks if t["TaskID"] == task_id), None)

# Funkcija za edit taska
def edit_task(task_id, **kwargs):
    task = get_task(task_id)
    if not task:
        return False
    for key, value in kwargs.items():
        if key in task:
            task[key] = value
    return True

def get_tasks():
    return tasks


def add_task(task_name, task_category, created_date, end_date,
             activation_date, assigned_to):
    """
    Adds a new task to the tasks list with auto-incremented TaskID.
    """
    # Find max ID
    max_id = max([task["TaskID"] for task in tasks]) if tasks else 100

    new_task = {
        "TaskID": max_id + 1,
        "TaskName": task_name,
        "TaskCategory": task_category,
        "CreatedDate": created_date,
        "EndDate": end_date,
        "ActivationDate": activation_date,
        "AssignedTo": assigned_to
    }

    tasks.append(new_task)
    return new_task

# Funkcija za brisanje taska
def delete_task(task_id):
    global tasks
    tasks = [t for t in tasks if t["TaskID"] != task_id]
    return True


holidays =[
    {
        "EmployeeID": 1,
        "Name": "Branislav Tomic",
        "FreeDays":25,
        "Abesence":[{'id':'qweesd', 'start':'2025-01-01', 'end':'2025-01-15', "type":"holiday"},{'id':'qw678eesd','start':'2025-02-02', 'end':'2025-02-15', "type":"holiday"}, {'id':'jklhjkdfgwe','start':'2025-03-02', 'end':'2025-03-02', "type":"freeDay"},{'id':'jklfytg453sdf','start':'2025-05-02', 'end':'2025-05-09', "type":"homeOffice"} ]
    },
    {
        "EmployeeID": 2,
        "Name": "Nenad Babic",
        "FreeDays":25,
        "Abesence":[{'id':'qweesvxcfssd','start':'2025-01-01', 'end':'2025-01-15', "type":"holiday"},{'id':'qwesdfgwe234esd','start':'2025-02-02', 'end':'2025-02-15', "type":"holiday"}, {'id':'qwererwe435jesd','start':'2025-03-02', 'end':'2025-03-02', "type":"freeDay"},{'id':'xcvvvbncwexc','start':'2025-04-02', 'end':'2025-04-07', "type":"homeOffice"} ]
    },
     {
        "EmployeeID": 3,
        "Name": "Nenad Todorovic",
        "FreeDays":25,
        "Abesence":[{'id':'qwee23454sd','start':'2025-03-01', 'end':'2025-03-10', "type":"holiday"},{'id':'6784534g','start':'2025-02-02', 'end':'2025-02-15', "type":"holiday"}, {'id':'qw8934hjjkeesd','start':'2025-03-02', 'end':'2025-03-02', "type":"freeDay"},{'id':'iopftyxcv3d','start':'2025-03-02', 'end':'2025-03-02', "type":"homeOffice"} ]
    }
]


employees = [
        {
            "EmployeeID": 1,
            "Name": "Marko Markovic",
            "Tasks": [
                {"TaskID": 101, "Title": "Fix API bug", "DateTo": "2025-02-03"},
                {"TaskID": 102, "Title": "Prepare report", "DateTo": "2025-02-10"},
            ]
        },
        {
            "EmployeeID": 2,
            "Name": "Jovana Petrovic",
            "Tasks": [
                {"TaskID": 103, "Title": "Database cleanup", "DateTo": "2025-01-28"}
            ]
        }
    ]


unassigned_tasks = [
        {"TaskID": 201, "Title": "Inventory check", "DateTo": "2025-03-02"},
        {"TaskID": 202, "Title": "Email campaign", "DateTo": "2025-02-12"}
    ]


task_comments = {

        "TaskID": 101,
        "TaskName": "Prepare Monthly Report",
        "DueDate": "2025-01-15",
        "Comments": [
            {
                "CommentID": 1,
                "UserName": "Marko",
                "Message": "Hej, počeo sam da radim na izveštaju.",
                "CreatedAt": "2025-01-10 10:32",
                "IsMine": False
            },
            {
                "CommentID": 2,
                "UserName": "Bane",
                "Message": "Super! Ja ću dodati finansijski deo.",
                "CreatedAt": "2025-01-10 10:35",
                "IsMine": True
            },
            {
                "CommentID": 3,
                "UserName": "Marko",
                "Message": "Odlično, javi ako ti treba nešto.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": False
            },
             {
                "CommentID": 4,
                "UserName": "Bane",
                "Message": "Super! Ja ću dodati finansijski deo 2.",
                "CreatedAt": "2025-01-10 10:35",
                "IsMine": True
            },
            {
                "CommentID": 5,
                "UserName": "Bane",
                "Message": "Odlično, javi ako ti treba nešto 3.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": True
            },
                       {
                "CommentID": 6,
                "UserName": "Bane",
                "Message": "Odlično, javi ako ti treba nešto 4.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": True
            },
             {
                "CommentID": 7,
                "UserName": "Bane",
                "Message": "Super! Ja ću dodati finansijski deo 2.",
                "CreatedAt": "2025-01-10 10:35",
                "IsMine": True
            },
            {
                "CommentID": 8,
                "UserName": "Bane",
                "Message": "Odlično, javi ako ti treba nešto 3.",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": True
            },
                       {
                "CommentID": 9,
                "UserName": "Bane",
                "Message": "Jebem li ti majku bezobraznu, kako si mogao to da uradis smrade jedan?",
                "CreatedAt": "2025-01-10 10:40",
                "IsMine": True
            }
        ]
    }

holidays_set = {
    # 2025. Praznici koje ste inicijalno uneli (ostavljam ih u setu radi kompletnosti)
    date(2025, 1, 1),
    date(2025, 1, 7),
    date(2025, 2, 15),
    date(2025, 2, 16),
    
    # 2026. Fiksni državni i verski praznici
    date(2026, 1, 1), # Nova godina (četvrtak)
    date(2026, 1, 2), # Nova godina (petak)
    date(2026, 1, 7), # Božić (sreda)
    
    # Sretenje - Dan državnosti Srbije
    date(2026, 2, 15), # Dan državnosti (nedelja)
    date(2026, 2, 16), # Dan državnosti (ponedeljak - premešta se jer 15. februar pada u nedelju)
    
    # Praznik rada
    date(2026, 5, 1),  # Praznik rada (petak)
    date(2026, 5, 2),  # Praznik rada (subota)
    
    date(2026, 5, 9),  # Dan pobede (subota)
    date(2026, 11, 11),# Dan primirja (sreda)
    
    # 2026. Uskršnji praznici (Pravoslavni - Uskrs je 19. aprila)
    date(2026, 4, 17), # Veliki petak
    date(2026, 4, 18), # Velika subota (radni dan, ali je ovde uvrštena da se obuhvati ceo period verskih praznika, iako je Uskrs neradni od Velikog petka do ponedeljka. Uklonite ako Vam ne treba.)
    date(2026, 4, 19), # Uskrs (nedelja)
    date(2026, 4, 20), # Uskršnji ponedeljak
}

budget_config = {
    'data': [        
        ['SW-DEV', 'Website development', 'TechCorp', 50000, 15000, 120000, 10000, 5000, 'Yes'],
        ['SW-LIC', 'Office 365 licenses', 'Microsoft', 12000, 11000, 0, 0, 0, 'Yes'],
        ['HW-EQUIP', 'New laptops', 'Dell Inc.', 45000, 25000, 10000, 0, 0, 'Pending'],
        ['HOSTING', 'Cloud server hosting', 'AWS', 24000, 6000, 3000, 3000, 3000, 'Yes'],
        ['SERVICES', 'Consulting services', 'BCG', 80000, 20000, 30000, 20000, 10000, 'No'],
        ['EDU', 'Employee training', 'Coursera', 15000, 5000, 5000, 5000, 0, 'Yes'],
        ['HW-LIC', 'Windows licenses', 'Microsoft', 10000, 10000, 0, 0, 0, 'Yes'],
        ['SW-DEV', 'Mobile app development', 'AppWorks', 75000, 25000, 25000, 12000, 0, 'Pending'],
        ['OTHER', 'Team building event', 'EventPlus', 8000, 6000, 0, 0, 0, 'Yes'],
        ['SERVICES', 'Legal services', 'LawPartner', 30000, 10000, 10000, 0, 0, 'No']
    ],
    'columns': [
        {'type': 'dropdown', 'title': 'Category','source': ['SW-DEV', 'SW-LIC', 'HW-EQUIP','HW-LIC','HOSTING', 'SERVICES','EDU','OTHER' ]},            
        {'type': 'text', 'title': 'Description'},
        {'type': 'text', 'title': 'Vendor name'},        
        {'type': 'numeric', 'title': 'Budget', 'mask': '#.##0,00 €', 'decimal': ','},    
        {'type': 'numeric', 'title': 'Payed Q1', 'mask': '#.##0,00 €', 'decimal': ','},    
        {'type': 'numeric', 'title': 'Payed Q2', 'mask': '#.##0,00 €', 'decimal': ','},    
        {'type': 'numeric', 'title': 'Payed Q3', 'mask': '#.##0,00 €', 'decimal': ','},    
        {'type': 'numeric', 'title': 'Payed Q4', 'mask': '#.##0,00 €', 'decimal': ','},    
        {'type': 'dropdown', 'title': 'Status', 'source': ['Yes', 'No', 'Pending']}
    ]
}

my_notes = [
    {'date':'2025-01-01', 'title':'novi web shop', 
     'content':'na sastanku smo dogovorili sledece zadatke: 1: da se kreira tim; 2. da se pozovu dobavljaci'},
    {'date':'2025-01-02', 'title':'novi app', 
     'content':'na sastanku smo diskutovali opcije, ali nije bilo nikakvog zaljucka'}
]

goals = [
    {
        "id": 1,
        "EmployeeID": "1",
        "EmployeeName": "Marko Marković",
        "GoalType": "Q1",
        "GoalDescription": "Increase sales by 20% in Q1"
    },
    {
        "id": 2,
        "EmployeeID": "2",
        "EmployeeName": "Marko Marković",
        "GoalType": "Q3",
        "GoalDescription": "Complete advanced training course"
    },
    {
        "id": 3,
        "EmployeeID": "3",
        "EmployeeName": "Ana Anić",
        "GoalType": "Q2",
        "GoalDescription": "Launch new marketing campaign"
    }
]

aichat_history = {} 

kanban_data = {
    
    "boards": [
        {
            "id": "board1",
            "name": "My project 1",
            "lists": [
                {
                    "id": "list1",
                    "name": "To Do",
                    "cards": [
                        {"id": "card1", "title": "Task 1", "description": "Description for task 1"},
                        {"id": "card2", "title": "Task 2", "description": "Description for task 2"}
                    ]
                },
                {
                    "id": "list2",
                    "name": "In Progress",
                    "cards": [
                        {"id": "card3", "title": "Task 3", "description": "Description for task 3"}
                    ]
                },
                {
                    "id": "list3",
                    "name": "Done",
                    "cards": []
                }
            ]
        },
               {
            "id": "board2",
            "name": "My project 2",
            "lists": [
                {
                    "id": "list11",
                    "name": "To Do",
                    "cards": [
                        {"id": "card11", "title": "Task 11", "description": "Description for task 11"},
                        {"id": "card12", "title": "Task 22", "description": "Description for task 22"}
                    ]
                },
                {
                    "id": "list2",
                    "name": "In Progress",
                    "cards": [
                        {"id": "card13", "title": "Task 33", "description": "Description for task 33"}
                    ]
                },
                {
                    "id": "list13",
                    "name": "Done",
                    "cards": []
                }
            ]
        }
    ]
}

dashboardList = [  
        {
        "prompt": "i have problem with iphone",  
        "functionCallJsonDesc":{      
        "name": "functionCallJsonDesc",
        "description": "Process a customer support ticket request",
        "parameters": {
            "type": "object",
            "properties": {
                "ticketType": {
                "type": "string",
                "enum": ["HW", "SW", "MOBILE", "NETWORK", "OTHER"]
                },
                "reason": {
                "type": "string",
                "enum": ["Error", "Information", "OTHER"]
                },
                "system": {
                "type": "string",
                "enum": ["SAP", "WINDOWS", "OTHER"]
                }
            },
                "required": ["ticketType", "reason", "system"]            
            }
        },
        "JinjaTemplate": '<div class="card"><div class="card-header"><strong>Support ticket</strong></div><div class="card-body"><p><strong>Ticket type:</strong>{{ ticketType | default("N/A") }}</p><p><strong>Reason:</strong>   {{ reason | default("N/A") }}</p><p><strong>System:</strong>{{ system | default("N/A") }}</p></div></div>'
    },
        {
        "prompt": "i cannot login to SAP system, i forgot password",  
        "functionCallJsonDesc":{      
        "name": "functionCallJsonDesc",
        "description": "Process a customer support ticket request",
        "parameters": {
            "type": "object",
            "properties": {
                "ticketType": {
                "type": "string",
                "enum": ["HW", "SW", "MOBILE", "NETWORK", "OTHER"]
                },
                "reason": {
                "type": "string",
                "enum": ["Error", "Information", "OTHER"]
                },
                "system": {
                "type": "string",
                "enum": ["SAP", "WINDOWS", "OTHER"]
                }
            },
                "required": ["ticketType", "reason", "system"]            
            }
        },
        "JinjaTemplate": '<div class="card"><div class="card-header"><strong>Support ticket</strong></div><div class="card-body"><p><strong>Ticket type:</strong>{{ ticketType | default("N/A") }}</p><p><strong>Reason:</strong>   {{ reason | default("N/A") }}</p><p><strong>System:</strong>{{ system | default("N/A") }}</p></div></div>'
    }

]