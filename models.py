import uuid
from datetime import datetime
from database import db  # OVO JE KLJUČNO
# -------------------------------------------------
# BASE MODEL (ZA SVE)
# -------------------------------------------------
class BaseModel(db.Model):
    __abstract__ = True

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def primary_key(cls):
        return cls.__mapper__.primary_key[0].key




# -------------------------------------------------
# COMPANY
# -------------------------------------------------
class Company(BaseModel):
    __tablename__ = 'Company'

    __fillable__ = {'CompanyName', 'JsonData'}
    __readonly__ = {'ID'}

    ID = db.Column(db.BigInteger, primary_key=True)
    CompanyName = db.Column(db.String(500))
    JsonData = db.Column(db.Text)


# -------------------------------------------------
# TEAM
# -------------------------------------------------
class Team(BaseModel):
    __tablename__ = 'Team'

    __fillable__ = {'Name', 'JsonData', 'CompanyID'}
    __readonly__ = {'ID'}

    ID = db.Column(db.BigInteger, primary_key=True)
    Name = db.Column(db.String(200))
    JsonData = db.Column(db.Text)

    CompanyID = db.Column(db.BigInteger, db.ForeignKey('Company.ID'), nullable=False)


# -------------------------------------------------
# TEAM MEMBER
# -------------------------------------------------
class TeamMember(BaseModel):
    __tablename__ = 'TeamMember'

    __fillable__ = {'Name', 'Email', 'Role', 'JsonData', 'TeamID','Password'}
    __readonly__ = {'ID', 'CreatedAt'}

    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Name = db.Column(db.String(50))
    Email = db.Column(db.String(100))
    Role = db.Column(db.String(30))
    JsonData = db.Column(db.Text)
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    TeamID = db.Column(db.BigInteger, db.ForeignKey('Team.ID'), nullable=False)
    Password = db.Column(db.String(1000))
    NeedPasswordChange = db.Column(db.Boolean, default=True, nullable=True)
    Suspended = db.Column(db.Boolean, default=False, nullable=True)


# -------------------------------------------------
# TASK CATEGORIES
# -------------------------------------------------
class TaskCategories(BaseModel):
    __tablename__ = 'TaskCategories'

    __fillable__ = {'Name', 'Description', 'TeamID'}
    __readonly__ = {'ID'}

    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Name = db.Column(db.String(300))
    Description = db.Column(db.String(500))
    TeamID = db.Column(db.BigInteger, db.ForeignKey('Team.ID'))


# -------------------------------------------------
# TASK
# -------------------------------------------------
class Task(BaseModel): # ili db.Model, zavisno od tvoje strukture
    __tablename__ = 'Task'

    # ID je bigint prema tvom SQL-u, ali ako koristiš UUID-e, proveri da li je to namerno
    ID = db.Column(db.BigInteger, primary_key=True)
    Name = db.Column(db.String(500))
    Description = db.Column(db.String(500))
    TaskCategoryID = db.Column(db.String(36), db.ForeignKey('TaskCategories.ID'))
    ProjectName = db.Column(db.String(50))
    Status = db.Column(db.String(50))
    TaskCommentsJSON = db.Column(db.Text) # nvarchar(max)
    ActivationDate = db.Column(db.Date)
    
    # Ovo je sada tvoj strani ključ ka TeamMember
    AssignedTo = db.Column(db.String(36), db.ForeignKey('TeamMember.ID'))

    ArchiveDate = db.Column(db.DateTime, default=datetime.now)
    ClosingNote = db.Column(db.String(4000))
    
    EndDate = db.Column(db.Date)
    DateLog = db.Column(db.DateTime, default=datetime.now)
    TeamID  = db.Column(db.BigInteger)

    # Relacija za lakši pristup (npr. task.category.Name)
    category = db.relationship('TaskCategories', backref='tasks')
    assignee = db.relationship('TeamMember', backref='assigned_tasks')

# -------------------------------------------------
# COMMENTS
# -------------------------------------------------
class TaskComment(BaseModel):
    __tablename__ = 'TaskComment' # Proveri da li je TaskComment (jednina) kao u tvojoj skripti

    id = db.Column('ID', db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column('TaskID', db.BigInteger, db.ForeignKey('Task.ID'), nullable=False)
    user_id = db.Column('UserID', db.String(36), db.ForeignKey('TeamMember.ID'), nullable=False)
    message = db.Column('Message', db.Text, nullable=False)
    created_at = db.Column('CreatedAt', db.DateTime, default=datetime.utcnow)

    # Relacije (opciono, ali preporučljivo za lakši rad)
    # Ovo ti omogućava da kucaš comment.author.Name
    author = db.relationship('TeamMember', backref='task_comments')
    task = db.relationship('Task', backref='all_comments')


# -------------------------------------------------
# NOTES
# -------------------------------------------------
class Notes(BaseModel):
    __tablename__ = 'Notes'

    __fillable__ = {'NoteDate', 'NoteContent', 'TeamMemberID'}
    __readonly__ = {'ID', 'DateLog'}

    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Koristimo db.Date jer ti iz forme stiže čist datum (2026-02-09)
    NoteDate = db.Column(db.Date, nullable=False) 
    NoteTitle = db.Column(db.String(500))
    NoteContent = db.Column(db.String(500))
    
    # DateLog ostaje DateTime, ali bez zagrada kod datetime.now
    DateLog = db.Column(db.DateTime, default=datetime.now)

    TeamMemberID = db.Column(db.String(36), db.ForeignKey('TeamMember.ID'), nullable=False)


# -------------------------------------------------
# GOAL
# -------------------------------------------------
class Goal(BaseModel):
    __tablename__ = 'Goal'

    __fillable__ = {'JsonData', 'GoalType', 'Year', 'Description', 'TeamMemberID'}
    __readonly__ = {'ID'}

    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    JsonData = db.Column(db.Text)
    GoalType = db.Column(db.String(50))
    Year = db.Column(db.Integer, default=lambda: datetime.utcnow().year)
    Description = db.Column(db.String(500))

    TeamMemberID = db.Column(db.String(36), db.ForeignKey('TeamMember.ID'))


# -------------------------------------------------
# CALENDAR EVENTS
# -------------------------------------------------
class CalendarEvents(BaseModel):
    __tablename__ = 'CalendarEvents'

    __fillable__ = {'JsonData', 'TeamMemberID'}
    __readonly__ = {'ID'}

    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    JsonData = db.Column(db.String(4000))
    TeamMemberID = db.Column(db.String(36), db.ForeignKey('TeamMember.ID'))


# -------------------------------------------------
# BUDGET
# -------------------------------------------------
class Budget(BaseModel):
    __tablename__ = 'Budget'

    __fillable__ = {'JsonData', 'TeamID'}
    __readonly__ = {'ID'}

    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    JsonData = db.Column(db.String(50))
    TeamID = db.Column(db.BigInteger, db.ForeignKey('Team.ID'))


# -------------------------------------------------
# AI CONFIG
# -------------------------------------------------
class AIConfig(BaseModel):
    __tablename__ = 'AIConfig'

    __fillable__ = {'JsonData', 'TeamID'}
    __readonly__ = {'ID'}

    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    JsonData = db.Column(db.Text)
    TeamID = db.Column(db.BigInteger, db.ForeignKey('Team.ID'))

# -------------------------------------------------
# TEAM KNOWLEDGE
# -------------------------------------------------

class TeamKnowledge(BaseModel):
    __tablename__ = 'TeamKnowledge'

    # Definišemo koja polja se mogu masovno dodeljivati, a koja su samo za čitanje
    __fillable__ = {'TeamID', 'FileName', 'FileContent', 'Description','LastProcessedAt'}
    __readonly__ = {'ID'}

    # ID kao primarni ključ - koristimo String(36) radi konzistentnosti sa tvojim AIConfig primerom
    # Ako SQL Server zahteva striktno uniqueidentifier, možemo zameniti sa UNIQUEIDENTIFIER
    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        
    FileName = db.Column(db.Unicode(500), nullable=True)
    FileContent = db.Column(db.Text, nullable=True)
    Description = db.Column(db.Unicode(500), nullable=True)
    TeamID = db.Column(db.BigInteger, db.ForeignKey('Team.ID'))
    LastProcessedAt = db.Column(db.DateTime, nullable=True)
    DateLog = db.Column(db.DateTime, default=datetime.now)

class CompanyKnowledge(BaseModel):
    __tablename__ = 'CompanyKnowledge'

    # Definišemo dozvoljena polja za unos i readonly polja radi sigurnosti
    __fillable__ = {'CompanyID', 'FileName', 'FileContent', 'Description','LastProcessedAt'}
    __readonly__ = {'ID'}

    # ID primarni ključ - konzistentno sa AIConfig i TeamKnowledge modelima
    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Mapiranje prema SQL skriptu    
    FileName = db.Column(db.Unicode(200), nullable=True) # nvarchar(200)
    FileContent = db.Column(db.Text, nullable=True)      # text
    Description = db.Column(db.Unicode(500), nullable=True) # nvarchar(500)
    CompanyID = db.Column(db.BigInteger, db.ForeignKey('Company.ID'))
    LastProcessedAt = db.Column(db.DateTime, nullable=True)
    DateLog = db.Column(db.DateTime, default=datetime.now)


class KnowledgeEmbedding(BaseModel):
    __tablename__ = 'KnowledgeEmbeddings'
    
    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    KnowledgeID = db.Column(db.String(36), nullable=False)
    Scope = db.Column(db.Unicode(50), nullable=False)
    ChunkText = db.Column(db.UnicodeText, nullable=False)
    Embedding = db.Column(db.LargeBinary, nullable=False) # Za čuvanje numpy binarne verzije
    # Dodaj ove dve kolone
    TeamID = db.Column(db.BigInteger, nullable=True)
    CompanyID = db.Column(db.BigInteger, nullable=True)


class Prompt(BaseModel):
    __tablename__ = 'Prompt'

    # Polja koja se mogu masovno popunjavati
    __fillable__ = {
        'Prompt', 
        'Model', 
        'StaticContextIncluded', 
        'DynamicContextIncluded', 
        'ChatHistory', 
        'TeamMemberID', 
        'CreatedDate',
        'SavedMessage'
    }
    
    # Polja koja su sistemska i ne menjaju se direktno
    __readonly__ = {'ID'}

    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Prompt = db.Column(db.String(4000), nullable=False)
    Model = db.Column(db.String(100))
    StaticContextIncluded = db.Column(db.Boolean, nullable=False, default=False)
    DynamicContextIncluded = db.Column(db.Boolean, nullable=False, default=False)
    ChatHistory = db.Column(db.Text) # Mapira se na nvarchar(max)
    TeamMemberID = db.Column(db.String(36), db.ForeignKey('TeamMember.ID'), nullable=False)
    CreatedDate = db.Column(db.DateTime, default=datetime.utcnow)
    SavedMessage = db.Column(db.Text)

class ConfigData(BaseModel):
    __tablename__ = 'ConfigData'
    
    __fillable__ = {
        'ConfigData', 
        'TeamID', 
        'CompanyID', 
        'DateLog'
    }    
    
    __readonly__ = {'ID'}    
    ID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))    
    ConfigData = db.Column(db.Text, nullable=True)     
    TeamID = db.Column(db.BigInteger, db.ForeignKey('Team.ID'), nullable=True)
    CompanyID = db.Column(db.BigInteger, db.ForeignKey('Company.ID'), nullable=True)        
    DateLog = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class DashboardCard(BaseModel):
    __tablename__ = 'DashboardCard'
    __fillable__ = {
        'AuthorID', 
        'TeamID', 
        'Title', 
        'CardType',
        'QueryOrPrompt',
        'Model',
        'Size',
        'Position',
        'CreatedAt'
    }    
    
    __readonly__ = {'ID'}   

    # ID je primarni ključ, IDENTITY(1,1) u MSSQL-u se mapira kao autoincrement=True
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)    
    # AuthorID je UNIQUEIDENTIFIER, u Pythonu radimo sa stringom od 36 karaktera
    AuthorID = db.Column(db.String(36), nullable=False, index=True)
    TeamID = db.Column(db.BigInteger, nullable=False, index=True)
    Title = db.Column(db.Unicode(100), nullable=False)
    CardType = db.Column(db.Unicode(20), nullable=False)
    QueryOrPrompt = db.Column(db.UnicodeText, nullable=False)
    Model = db.Column(db.Unicode(150), server_default='gpt-4o-mini')
    Size = db.Column(db.Integer, server_default='3')
    Position = db.Column(db.Integer, server_default='0')
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())

class AICallLog(BaseModel):
    __tablename__ = 'AI_Call_Log'
    __fillable__ = {
        'TeamMemberID', 
        'Model', 
        'InputTokens', 
        'OutputTokens',
        'InputPricePer1K',
        'OutputPricePer1K',
        'EstimatedPrice',
        'RequestId',
        'ExecutionTimeMs',
        'ExecutionStatus',
        'ErrorMessage',
        'PromptText',
        'ResponseText'
    }    
    __readonly__ = {'Id', 'TotalTokens', 'CreatedAt'}    
    
    Id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    TeamMemberID = db.Column(db.String(100), nullable=False)
    Model = db.Column(db.String(200), nullable=False)
    InputTokens = db.Column(db.Integer, nullable=False, default=0)
    OutputTokens = db.Column(db.Integer, nullable=False, default=0)
    TotalTokens = db.Column(db.Integer, db.Computed("InputTokens + OutputTokens"), nullable=True)
    InputPricePer1K = db.Column(db.Numeric(10, 6), nullable=False)
    OutputPricePer1K = db.Column(db.Numeric(10, 6), nullable=False)
    EstimatedPrice = db.Column(db.Numeric(18, 6), nullable=False)
    RequestId = db.Column(db.String(200), nullable=True)
    ExecutionTimeMs = db.Column(db.Integer, nullable=True)
    ExecutionStatus = db.Column(db.String(50), nullable=False) # success / error
    ErrorMessage = db.Column(db.Text, nullable=True)
    PromptText = db.Column(db.Text, nullable=True)
    ResponseText = db.Column(db.Text, nullable=True)
    CreatedAt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class RiskRegister(BaseModel):
    __tablename__ = 'RiskRegister'
    __fillable__ = {'Title','RiskDescription','Category','Probability','Impact','OwnerID',
                    'RiskStatus','MitigationStrategy','ContingencyPlan','AI_Insight_Summary',
                    'Last_AI_Review','DateIdentified','DueDate','UpdatedAt','TeamID'}    
    __readonly__ = {'RiskID'}    
    
    RiskID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Title = db.Column(db.String(200), nullable=False)
    RiskDescription = db.Column(db.Text, nullable=True)
    Category = db.Column(db.String(50), nullable=True)   
    Probability = db.Column(db.Integer, nullable=True)
    Impact = db.Column(db.Integer, nullable=True, default=1)
    
    # RiskScore je PERSISTED u SQL-u
    RiskScore = db.Column(db.Integer, db.Computed("Probability * Impact"), nullable=True)    
    OwnerID = db.Column(db.String(36), nullable=False)
    RiskStatus = db.Column(db.String(20), nullable=True)
    
    MitigationStrategy = db.Column(db.Text, nullable=True,default="")
    ContingencyPlan = db.Column(db.Text, nullable=True)
    
    # AI polja
    AI_Insight_Summary = db.Column(db.Text, nullable=True)
    Last_AI_Review = db.Column(db.DateTime, nullable=True)
    
    # Datumi
    DateIdentified = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    DueDate = db.Column(db.DateTime, nullable=True)
    UpdatedAt = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Tim (povezan sa tvojom Team tabelom preko BIGINT ID-ja)
    TeamID = db.Column(db.BigInteger, db.ForeignKey('Team.ID'), nullable=False)

class RiskHistory(db.Model):
    __tablename__ = 'RiskHistory'
    __fillable__ = {'Title','RiskDescription','Category','Probability','Impact','RiskScore','RiskStatus','MitigationStrategy','ChangedBy','ChangeNotes','Timestamp'}    
    __readonly__ = {'RiskHistoryID'}    
    
    RiskHistoryID = db.Column(db.BigInteger, primary_key=True)
    RiskID = db.Column(db.String(36), db.ForeignKey('RiskRegister.RiskID'), nullable=False)
    
    # Podaci koje pratimo
    Probability = db.Column(db.Integer)
    Impact = db.Column(db.Integer)
    RiskScore = db.Column(db.Integer, db.Computed("Probability * Impact"), nullable=True)  
    RiskStatus = db.Column(db.String(20))
    MitigationStrategy = db.Column(db.Text, nullable=True,default="") 
    
    # Metapodaci promene
    ChangedBy = db.Column(db.String(36), nullable=False) # ID korisnika
    ChangeNotes = db.Column(db.Text, nullable=True) # Npr. "Status promenjen u Mitigated"
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacija za lakši pristup
    risk = db.relationship('RiskRegister', backref=db.backref('history', lazy=True))
    


    
   
    
  