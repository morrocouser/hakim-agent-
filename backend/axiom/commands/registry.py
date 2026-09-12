# Command Registry - Core command management system

from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from enum import Enum
import re


class CommandGroup(Enum):
    """Command categories"""
    SYSTEM = "system"
    AGENT = "agent"
    CODE = "code"
    PROJECT = "project"
    GIT = "git"
    SHELL = "shell"
    SEARCH = "search"
    FILES = "files"
    DATABASE = "database"
    DOCKER = "docker"
    CLOUD = "cloud"
    AI = "ai"
    MEDIA = "media"
    PRODUCTIVITY = "productivity"
    SECURITY = "security"
    BROWSER = "browser"
    MEMORY = "memory"
    TOOLS = "tools"
    MCP = "mcp"
    AUTOMATION = "automation"
    MONITORING = "monitoring"
    ADVANCED = "advanced"


@dataclass
class Command:
    """Represents a single slash command"""
    name: str
    description: str
    group: CommandGroup
    handler: Optional[Callable] = None
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    hidden: bool = False
    requires_context: bool = False


class CommandRegistry:
    """Central registry for all slash commands"""
    
    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._groups: dict[CommandGroup, list[str]] = {}
        self._initialize_commands()
    
    def _initialize_commands(self):
        """Initialize all commands"""
        # System commands
        self.register(Command(
            name="/help",
            description="Show help for all commands or a specific command",
            group=CommandGroup.SYSTEM,
            usage="/help [command]",
            examples=["/help", "/help /code", "/help git"]
        ))
        self.register(Command(
            name="/about",
            description="Show information about hakimagent",
            group=CommandGroup.SYSTEM,
            usage="/about"
        ))
        self.register(Command(
            name="/version",
            description="Show current version",
            group=CommandGroup.SYSTEM,
            usage="/version"
        ))
        self.register(Command(
            name="/status",
            description="Show system status and health",
            group=CommandGroup.SYSTEM,
            usage="/status"
        ))
        self.register(Command(
            name="/config",
            description="View or modify configuration",
            group=CommandGroup.SYSTEM,
            usage="/config [key] [value]",
            examples=["/config", "/config model gpt-4"]
        ))
        self.register(Command(
            name="/settings",
            description="Manage user settings",
            group=CommandGroup.SYSTEM,
            usage="/settings [category]",
            examples=["/settings", "/settings theme dark"]
        ))
        self.register(Command(
            name="/models",
            description="List available AI models",
            group=CommandGroup.SYSTEM,
            usage="/models"
        ))
        self.register(Command(
            name="/providers",
            description="List available AI providers",
            group=CommandGroup.SYSTEM,
            usage="/providers"
        ))
        self.register(Command(
            name="/tools",
            description="List available tools",
            group=CommandGroup.SYSTEM,
            usage="/tools [category]"
        ))
        self.register(Command(
            name="/skills",
            description="List available skills",
            group=CommandGroup.SYSTEM,
            usage="/skills [category]"
        ))
        self.register(Command(
            name="/find-skills",
            description="Search and find skills by keyword or domain",
            group=CommandGroup.SYSTEM,
            usage="/find-skills <query>",
            aliases=["/findskills", "/search-skills"],
            examples=["/find-skills python", "/find-skills react"]
        ))
        self.register(Command(
            name="/memory",
            description="View and manage memory",
            group=CommandGroup.SYSTEM,
            usage="/memory [action] [args]"
        ))
        self.register(Command(
            name="/context",
            description="View current context",
            group=CommandGroup.SYSTEM,
            usage="/context"
        ))
        self.register(Command(
            name="/logs",
            description="View system logs",
            group=CommandGroup.SYSTEM,
            usage="/logs [level] [lines]"
        ))
        self.register(Command(
            name="/health",
            description="Run health checks",
            group=CommandGroup.SYSTEM,
            usage="/health"
        ))
        self.register(Command(
            name="/reset",
            description="Reset current session",
            group=CommandGroup.SYSTEM,
            usage="/reset"
        ))
        self.register(Command(
            name="/restart",
            description="Restart the system",
            group=CommandGroup.SYSTEM,
            usage="/restart"
        ))
        self.register(Command(
            name="/exit",
            description="Exit the application",
            group=CommandGroup.SYSTEM,
            usage="/exit"
        ))
        
        # Agent commands
        self.register(Command(
            name="/plan",
            description="Create or view implementation plans",
            group=CommandGroup.AGENT,
            usage="/plan [action] [args]",
            examples=["/plan create", "/plan list", "/plan show 1"]
        ))
        self.register(Command(
            name="/think",
            description="Enable thinking mode for complex reasoning",
            group=CommandGroup.AGENT,
            usage="/think [on|off]",
            examples=["/think on", "/think off"]
        ))
        self.register(Command(
            name="/solve",
            description="Solve a problem step by step",
            group=CommandGroup.AGENT,
            usage="/solve [problem description]",
            examples=["/solve How to implement authentication"]
        ))
        self.register(Command(
            name="/run",
            description="Execute a task or script",
            group=CommandGroup.AGENT,
            usage="/run [task]",
            examples=["/run tests", "/run build"]
        ))
        self.register(Command(
            name="/execute",
            description="Execute a command or task",
            group=CommandGroup.AGENT,
            usage="/execute [command]"
        ))
        self.register(Command(
            name="/cancel",
            description="Cancel current operation",
            group=CommandGroup.AGENT,
            usage="/cancel"
        ))
        self.register(Command(
            name="/retry",
            description="Retry last failed operation",
            group=CommandGroup.AGENT,
            usage="/retry"
        ))
        self.register(Command(
            name="/continue",
            description="Continue paused operation",
            group=CommandGroup.AGENT,
            usage="/continue"
        ))
        self.register(Command(
            name="/pause",
            description="Pause current operation",
            group=CommandGroup.AGENT,
            usage="/pause"
        ))
        self.register(Command(
            name="/resume",
            description="Resume paused operation",
            group=CommandGroup.AGENT,
            usage="/resume"
        ))
        self.register(Command(
            name="/stop",
            description="Stop current operation",
            group=CommandGroup.AGENT,
            usage="/stop"
        ))
        self.register(Command(
            name="/queue",
            description="View or manage task queue",
            group=CommandGroup.AGENT,
            usage="/queue [action]",
            examples=["/queue list", "/queue clear"]
        ))
        self.register(Command(
            name="/tasks",
            description="View and manage tasks",
            group=CommandGroup.AGENT,
            usage="/tasks [action]",
            examples=["/tasks list", "/tasks add 'Fix bug'"]
        ))
        self.register(Command(
            name="/history",
            description="View command history",
            group=CommandGroup.AGENT,
            usage="/history [lines]"
        ))
        
        # Code commands
        self.register(Command(
            name="/code",
            description="Code-related operations",
            group=CommandGroup.CODE,
            usage="/code [action] [args]",
            examples=["/code generate", "/code review", "/code explain"]
        ))
        self.register(Command(
            name="/debug",
            description="Debug code or issues",
            group=CommandGroup.CODE,
            usage="/debug [issue]",
            examples=["/debug", "/debug 'TypeError in main.py'"]
        ))
        self.register(Command(
            name="/fix",
            description="Fix code issues",
            group=CommandGroup.CODE,
            usage="/fix [issue]",
            examples=["/fix", "/fix 'syntax error'"]
        ))
        self.register(Command(
            name="/explain",
            description="Explain code or concepts",
            group=CommandGroup.CODE,
            usage="/explain [code or concept]",
            examples=["/explain main.py", "/explain recursion"]
        ))
        self.register(Command(
            name="/refactor",
            description="Refactor code",
            group=CommandGroup.CODE,
            usage="/refactor [file or pattern]",
            examples=["/refactor main.py", "/refactor extract method"]
        ))
        self.register(Command(
            name="/review",
            description="Review code quality",
            group=CommandGroup.CODE,
            usage="/review [file or PR]",
            examples=["/review", "/review main.py", "/review pr 123"]
        ))
        self.register(Command(
            name="/optimize",
            description="Optimize code performance",
            group=CommandGroup.CODE,
            usage="/optimize [file or function]",
            examples=["/optimize", "/optimize main.py"]
        ))
        self.register(Command(
            name="/test",
            description="Run or create tests",
            group=CommandGroup.CODE,
            usage="/test [action] [args]",
            examples=["/test", "/test create", "/test run main"]
        ))
        self.register(Command(
            name="/benchmark",
            description="Run benchmarks",
            group=CommandGroup.CODE,
            usage="/benchmark [target]",
            examples=["/benchmark", "/benchmark main.py"]
        ))
        self.register(Command(
            name="/document",
            description="Generate documentation",
            group=CommandGroup.CODE,
            usage="/document [target]",
            examples=["/document", "/document main.py"]
        ))
        self.register(Command(
            name="/comment",
            description="Add or manage comments",
            group=CommandGroup.CODE,
            usage="/comment [action] [args]",
            examples=["/comment add", "/comment list"]
        ))
        self.register(Command(
            name="/generate",
            description="Generate code from specification",
            group=CommandGroup.CODE,
            usage="/generate [specification]",
            examples=["/generate REST API for users"]
        ))
        
        # Project commands
        self.register(Command(
            name="/project",
            description="Project management operations",
            group=CommandGroup.PROJECT,
            usage="/project [action] [args]",
            examples=["/project info", "/project create"]
        ))
        self.register(Command(
            name="/open",
            description="Open project or file",
            group=CommandGroup.PROJECT,
            usage="/open [path]",
            examples=["/open .", "/open main.py"]
        ))
        self.register(Command(
            name="/create",
            description="Create new project or file",
            group=CommandGroup.PROJECT,
            usage="/create [type] [name]",
            examples=["/create project myapp", "/create file main.py"]
        ))
        self.register(Command(
            name="/init",
            description="Initialize project",
            group=CommandGroup.PROJECT,
            usage="/init [template]",
            examples=["/init", "/init python"]
        ))
        self.register(Command(
            name="/build",
            description="Build project",
            group=CommandGroup.PROJECT,
            usage="/build [target]",
            examples=["/build", "/build production"]
        ))
        self.register(Command(
            name="/run-project",
            description="Run the project",
            group=CommandGroup.PROJECT,
            usage="/run-project [args]",
            examples=["/run-project", "/run-project --dev"]
        ))
        self.register(Command(
            name="/analyze",
            description="Analyze project structure",
            group=CommandGroup.PROJECT,
            usage="/analyze [target]",
            examples=["/analyze", "/analyze src/"]
        ))
        self.register(Command(
            name="/architecture",
            description="View or modify architecture",
            group=CommandGroup.PROJECT,
            usage="/architecture [view|modify]",
            examples=["/architecture view", "/architecture modify"]
        ))
        self.register(Command(
            name="/dependencies",
            description="Manage project dependencies",
            group=CommandGroup.PROJECT,
            usage="/dependencies [action]",
            examples=["/dependencies list", "/dependencies add lodash"]
        ))
        self.register(Command(
            name="/structure",
            description="View project structure",
            group=CommandGroup.PROJECT,
            usage="/structure [depth]",
            examples=["/structure", "/structure 2"]
        ))
        
        # Git commands
        self.register(Command(
            name="/git",
            description="Git operations",
            group=CommandGroup.GIT,
            usage="/git [command] [args]",
            examples=["/git status", "/git commit -m 'msg'"]
        ))
        self.register(Command(
            name="/commit",
            description="Create git commit",
            group=CommandGroup.GIT,
            usage="/commit [message]",
            examples=["/commit 'Fix bug'", "/commit"]
        ))
        self.register(Command(
            name="/push",
            description="Push to remote",
            group=CommandGroup.GIT,
            usage="/push [remote] [branch]",
            examples=["/push", "/push origin main"]
        ))
        self.register(Command(
            name="/pull",
            description="Pull from remote",
            group=CommandGroup.GIT,
            usage="/pull [remote] [branch]",
            examples=["/pull", "/pull origin main"]
        ))
        self.register(Command(
            name="/branch",
            description="Manage git branches",
            group=CommandGroup.GIT,
            usage="/branch [action] [name]",
            examples=["/branch list", "/branch create feature"]
        ))
        self.register(Command(
            name="/merge",
            description="Merge branches",
            group=CommandGroup.GIT,
            usage="/merge [branch]",
            examples=["/merge main", "/merge feature/auth"]
        ))
        self.register(Command(
            name="/tag",
            description="Manage git tags",
            group=CommandGroup.GIT,
            usage="/tag [action] [name]",
            examples=["/tag list", "/tag create v1.0.0"]
        ))
        self.register(Command(
            name="/pr",
            description="Pull request operations",
            group=CommandGroup.GIT,
            usage="/pr [action] [args]",
            examples=["/pr create", "/pr list", "/pr merge 123"]
        ))
        self.register(Command(
            name="/issues",
            description="Issue tracking",
            group=CommandGroup.GIT,
            usage="/issues [action] [args]",
            examples=["/issues list", "/issues create 'Bug'"]
        ))
        self.register(Command(
            name="/release",
            description="Create release",
            group=CommandGroup.GIT,
            usage="/release [version]",
            examples=["/release", "/release 1.0.0"]
        ))
        
        # Shell commands
        self.register(Command(
            name="/bash",
            description="Execute bash command",
            group=CommandGroup.SHELL,
            usage="/bash [command]",
            examples=["/bash ls -la", "/bash git status"]
        ))
        self.register(Command(
            name="/powershell",
            description="Execute PowerShell command",
            group=CommandGroup.SHELL,
            usage="/powershell [command]",
            examples=["/powershell Get-ChildItem"]
        ))
        self.register(Command(
            name="/cmd",
            description="Execute cmd command",
            group=CommandGroup.SHELL,
            usage="/cmd [command]",
            examples=["/cmd dir"]
        ))
        self.register(Command(
            name="/shell",
            description="Execute shell command",
            group=CommandGroup.SHELL,
            usage="/shell [command]",
            examples=["/shell ls"]
        ))
        self.register(Command(
            name="/npm",
            description="NPM operations",
            group=CommandGroup.SHELL,
            usage="/npm [command]",
            examples=["/npm install", "/npm run dev"]
        ))
        self.register(Command(
            name="/pnpm",
            description="PNPM operations",
            group=CommandGroup.SHELL,
            usage="/pnpm [command]",
            examples=["/pnpm install"]
        ))
        self.register(Command(
            name="/yarn",
            description="Yarn operations",
            group=CommandGroup.SHELL,
            usage="/yarn [command]",
            examples=["/yarn install"]
        ))
        self.register(Command(
            name="/bun",
            description="Bun operations",
            group=CommandGroup.SHELL,
            usage="/bun [command]",
            examples=["/bun install", "/bun run dev"]
        ))
        self.register(Command(
            name="/pip",
            description="Pip operations",
            group=CommandGroup.SHELL,
            usage="/pip [command]",
            examples=["/pip install requests"]
        ))
        self.register(Command(
            name="/cargo",
            description="Cargo operations",
            group=CommandGroup.SHELL,
            usage="/cargo [command]",
            examples=["/cargo build", "/cargo run"]
        ))
        self.register(Command(
            name="/go",
            description="Go operations",
            group=CommandGroup.SHELL,
            usage="/go [command]",
            examples=["/go run main.go", "/go build"]
        ))
        
        # Search commands
        self.register(Command(
            name="/search",
            description="Search files or content",
            group=CommandGroup.SEARCH,
            usage="/search [query]",
            examples=["/search 'function'", "/search files *.py"]
        ))
        self.register(Command(
            name="/web",
            description="Web search",
            group=CommandGroup.SEARCH,
            usage="/web [query]",
            examples=["/web Python best practices"]
        ))
        self.register(Command(
            name="/google",
            description="Google search",
            group=CommandGroup.SEARCH,
            usage="/google [query]",
            examples=["/google How to learn Python"]
        ))
        self.register(Command(
            name="/github",
            description="GitHub search",
            group=CommandGroup.SEARCH,
            usage="/github [query]",
            examples=["/github python web framework"]
        ))
        self.register(Command(
            name="/docs",
            description="Search documentation",
            group=CommandGroup.SEARCH,
            usage="/docs [query]",
            examples=["/docs FastAPI"]
        ))
        self.register(Command(
            name="/api",
            description="Search APIs",
            group=CommandGroup.SEARCH,
            usage="/api [query]",
            examples=["/api weather"]
        ))
        self.register(Command(
            name="/research",
            description="Research a topic",
            group=CommandGroup.SEARCH,
            usage="/research [topic]",
            examples=["/research machine learning"]
        ))
        self.register(Command(
            name="/find",
            description="Find files or patterns",
            group=CommandGroup.SEARCH,
            usage="/find [pattern]",
            examples=["/find *.py", "/find main"]
        ))
        
        # File commands
        self.register(Command(
            name="/read",
            description="Read file contents",
            group=CommandGroup.FILES,
            usage="/read [file]",
            examples=["/read main.py", "/read README.md"]
        ))
        self.register(Command(
            name="/write",
            description="Write to file",
            group=CommandGroup.FILES,
            usage="/write [file] [content]",
            examples=["/write main.py 'print hello'"]
        ))
        self.register(Command(
            name="/edit",
            description="Edit file",
            group=CommandGroup.FILES,
            usage="/edit [file] [line] [content]",
            examples=["/edit main.py 10 'new code'"]
        ))
        self.register(Command(
            name="/create-file",
            description="Create new file",
            group=CommandGroup.FILES,
            usage="/create-file [file] [content]",
            examples=["/create-file main.py 'print hello'"]
        ))
        self.register(Command(
            name="/delete",
            description="Delete file",
            group=CommandGroup.FILES,
            usage="/delete [file]",
            examples=["/delete temp.py"]
        ))
        self.register(Command(
            name="/move",
            description="Move or rename file",
            group=CommandGroup.FILES,
            usage="/move [source] [dest]",
            examples=["/move old.py new.py"]
        ))
        self.register(Command(
            name="/copy",
            description="Copy file",
            group=CommandGroup.FILES,
            usage="/copy [source] [dest]",
            examples=["/copy main.py backup.py"]
        ))
        self.register(Command(
            name="/rename",
            description="Rename file",
            group=CommandGroup.FILES,
            usage="/rename [old] [new]",
            examples=["/rename old.py new.py"]
        ))
        self.register(Command(
            name="/tree",
            description="Show directory tree",
            group=CommandGroup.FILES,
            usage="/tree [path] [depth]",
            examples=["/tree", "/tree src 3"]
        ))
        self.register(Command(
            name="/list",
            description="List directory contents",
            group=CommandGroup.FILES,
            usage="/list [path]",
            examples=["/list", "/list src"]
        ))
        
        # Database commands
        self.register(Command(
            name="/sql",
            description="Execute SQL query",
            group=CommandGroup.DATABASE,
            usage="/sql [query]",
            examples=["/sql SELECT * FROM users"]
        ))
        self.register(Command(
            name="/query",
            description="Execute database query",
            group=CommandGroup.DATABASE,
            usage="/query [query]",
            examples=["/query SELECT * FROM users"]
        ))
        self.register(Command(
            name="/schema",
            description="View database schema",
            group=CommandGroup.DATABASE,
            usage="/schema [table]",
            examples=["/schema", "/schema users"]
        ))
        self.register(Command(
            name="/migrate",
            description="Run database migrations",
            group=CommandGroup.DATABASE,
            usage="/migrate [action]",
            examples=["/migrate up", "/migrate down"]
        ))
        self.register(Command(
            name="/seed",
            description="Seed database",
            group=CommandGroup.DATABASE,
            usage="/seed [source]",
            examples=["/seed", "/seed test-data.json"]
        ))
        self.register(Command(
            name="/backup",
            description="Backup database",
            group=CommandGroup.DATABASE,
            usage="/backup [name]",
            examples=["/backup", "/backup backup-001"]
        ))
        self.register(Command(
            name="/restore",
            description="Restore database",
            group=CommandGroup.DATABASE,
            usage="/restore [backup]",
            examples=["/restore backup-001"]
        ))
        
        # Docker commands
        self.register(Command(
            name="/docker",
            description="Docker operations",
            group=CommandGroup.DOCKER,
            usage="/docker [command]",
            examples=["/docker ps", "/docker images"]
        ))
        self.register(Command(
            name="/compose",
            description="Docker Compose operations",
            group=CommandGroup.DOCKER,
            usage="/compose [command]",
            examples=["/compose up", "/compose down"]
        ))
        self.register(Command(
            name="/k8s",
            description="Kubernetes operations",
            group=CommandGroup.DOCKER,
            usage="/k8s [command]",
            examples=["/k8s get pods", "/k8s apply -f pod.yaml"]
        ))
        self.register(Command(
            name="/deploy",
            description="Deploy application",
            group=CommandGroup.DOCKER,
            usage="/deploy [target]",
            examples=["/deploy", "/deploy production"]
        ))
        self.register(Command(
            name="/build-image",
            description="Build Docker image",
            group=CommandGroup.DOCKER,
            usage="/build-image [name] [tag]",
            examples=["/build-image myapp latest"]
        ))
        self.register(Command(
            name="/monitor",
            description="Monitor services",
            group=CommandGroup.DOCKER,
            usage="/monitor [service]",
            examples=["/monitor", "/monitor api"]
        ))
        
        # Cloud commands
        self.register(Command(
            name="/aws",
            description="AWS operations",
            group=CommandGroup.CLOUD,
            usage="/aws [service] [command]",
            examples=["/aws s3 ls", "/aws ec2 describe-instances"]
        ))
        self.register(Command(
            name="/gcp",
            description="Google Cloud operations",
            group=CommandGroup.CLOUD,
            usage="/gcp [service] [command]",
            examples=["/gcp compute list"]
        ))
        self.register(Command(
            name="/azure",
            description="Azure operations",
            group=CommandGroup.CLOUD,
            usage="/azure [service] [command]",
            examples=["/azure vm list"]
        ))
        self.register(Command(
            name="/vercel",
            description="Vercel operations",
            group=CommandGroup.CLOUD,
            usage="/vercel [command]",
            examples=["/vercel deploy", "/vercel ls"]
        ))
        self.register(Command(
            name="/cloudflare",
            description="Cloudflare operations",
            group=CommandGroup.CLOUD,
            usage="/cloudflare [command]",
            examples=["/cloudflare dns list"]
        ))
        self.register(Command(
            name="/render",
            description="Render operations",
            group=CommandGroup.CLOUD,
            usage="/render [command]",
            examples=["/render deploy"]
        ))
        self.register(Command(
            name="/cloud",
            description="Cloud operations",
            group=CommandGroup.CLOUD,
            usage="/cloud [provider] [command]",
            examples=["/cloud aws s3 ls"]
        ))
        
        # AI commands
        self.register(Command(
            name="/chat",
            description="Start chat session",
            group=CommandGroup.AI,
            usage="/chat [topic]",
            examples=["/chat", "/chat about Python"]
        ))
        self.register(Command(
            name="/agent",
            description="Agent operations",
            group=CommandGroup.AI,
            usage="/agent [action]",
            examples=["/agent list", "/agent create"]
        ))
        self.register(Command(
            name="/reason",
            description="Reason through a problem",
            group=CommandGroup.AI,
            usage="/reason [problem]",
            examples=["/reason How to optimize this code"]
        ))
        self.register(Command(
            name="/reflect",
            description="Reflect on a topic",
            group=CommandGroup.AI,
            usage="/reflect [topic]",
            examples=["/reflect on code quality"]
        ))
        self.register(Command(
            name="/summarize",
            description="Summarize content",
            group=CommandGroup.AI,
            usage="/summarize [file or text]",
            examples=["/summarize main.py", "/summarize 'long text'"]
        ))
        self.register(Command(
            name="/translate",
            description="Translate text",
            group=CommandGroup.AI,
            usage="/translate [lang] [text]",
            examples=["/translate es Hello world"]
        ))
        self.register(Command(
            name="/prompt",
            description="Send prompt to AI",
            group=CommandGroup.AI,
            usage="/prompt [prompt]",
            examples=["/prompt Explain recursion"]
        ))
        self.register(Command(
            name="/rag",
            description="RAG operations",
            group=CommandGroup.AI,
            usage="/rag [action] [query]",
            examples=["/rag search 'machine learning'"]
        ))
        self.register(Command(
            name="/embed",
            description="Create embeddings",
            group=CommandGroup.AI,
            usage="/embed [text]",
            examples=["/embed 'Hello world'"]
        ))
        
        # Media commands
        self.register(Command(
            name="/image",
            description="Image operations",
            group=CommandGroup.MEDIA,
            usage="/image [action] [args]",
            examples=["/image generate 'logo'", "/image analyze image.png"]
        ))
        self.register(Command(
            name="/analyze-image",
            description="Analyze image",
            group=CommandGroup.MEDIA,
            usage="/analyze-image [image]",
            examples=["/analyze-image photo.jpg"]
        ))
        self.register(Command(
            name="/ocr",
            description="Extract text from image",
            group=CommandGroup.MEDIA,
            usage="/ocr [image]",
            examples=["/ocr scan.png"]
        ))
        self.register(Command(
            name="/generate-image",
            description="Generate image",
            group=CommandGroup.MEDIA,
            usage="/generate-image [description]",
            examples=["/generate-image 'sunset over mountains'"]
        ))
        self.register(Command(
            name="/edit-image",
            description="Edit image",
            group=CommandGroup.MEDIA,
            usage="/edit-image [image] [action]",
            examples=["/edit-image photo.jpg resize 800x600"]
        ))
        self.register(Command(
            name="/transcribe",
            description="Transcribe audio",
            group=CommandGroup.MEDIA,
            usage="/transcribe [audio]",
            examples=["/transcribe recording.mp3"]
        ))
        self.register(Command(
            name="/speech",
            description="Text to speech",
            group=CommandGroup.MEDIA,
            usage="/speech [text]",
            examples=["/speech 'Hello world'"]
        ))
        self.register(Command(
            name="/tts",
            description="Text to speech",
            group=CommandGroup.MEDIA,
            usage="/tts [text]",
            examples=["/tts 'Hello world'"]
        ))
        self.register(Command(
            name="/audio",
            description="Audio operations",
            group=CommandGroup.MEDIA,
            usage="/audio [action] [args]",
            examples=["/audio convert mp3 wav"]
        ))
        self.register(Command(
            name="/video",
            description="Video operations",
            group=CommandGroup.MEDIA,
            usage="/video [action] [args]",
            examples=["/video convert mp4 avi"]
        ))
        self.register(Command(
            name="/subtitles",
            description="Generate subtitles",
            group=CommandGroup.MEDIA,
            usage="/subtitles [video]",
            examples=["/subtitles video.mp4"]
        ))
        self.register(Command(
            name="/clips",
            description="Create video clips",
            group=CommandGroup.MEDIA,
            usage="/clips [video] [start] [end]",
            examples=["/clips video.mp4 00:00 00:30"]
        ))
        self.register(Command(
            name="/analyze-video",
            description="Analyze video",
            group=CommandGroup.MEDIA,
            usage="/analyze-video [video]",
            examples=["/analyze-video video.mp4"]
        ))
        
        # Productivity commands
        self.register(Command(
            name="/todo",
            description="Manage todo list",
            group=CommandGroup.PRODUCTIVITY,
            usage="/todo [action] [task]",
            examples=["/todo add 'Fix bug'", "/todo list", "/todo done 1"]
        ))
        self.register(Command(
            name="/calendar",
            description="Calendar operations",
            group=CommandGroup.PRODUCTIVITY,
            usage="/calendar [action]",
            examples=["/calendar today", "/calendar add 'Meeting'"]
        ))
        self.register(Command(
            name="/meeting",
            description="Meeting operations",
            group=CommandGroup.PRODUCTIVITY,
            usage="/meeting [action]",
            examples=["/meeting schedule", "/meeting notes"]
        ))
        self.register(Command(
            name="/report",
            description="Generate report",
            group=CommandGroup.PRODUCTIVITY,
            usage="/report [type]",
            examples=["/report daily", "/report weekly"]
        ))
        self.register(Command(
            name="/email",
            description="Email operations",
            group=CommandGroup.PRODUCTIVITY,
            usage="/email [action]",
            examples=["/email send", "/email list"]
        ))
        self.register(Command(
            name="/notes",
            description="Manage notes",
            group=CommandGroup.PRODUCTIVITY,
            usage="/notes [action]",
            examples=["/notes add 'Important'", "/notes list"]
        ))
        
        # Security commands
        self.register(Command(
            name="/security",
            description="Security operations",
            group=CommandGroup.SECURITY,
            usage="/security [action]",
            examples=["/security scan", "/security audit"]
        ))
        self.register(Command(
            name="/audit",
            description="Security audit",
            group=CommandGroup.SECURITY,
            usage="/audit [target]",
            examples=["/audit", "/audit src/"]
        ))
        self.register(Command(
            name="/scan",
            description="Security scan",
            group=CommandGroup.SECURITY,
            usage="/scan [target]",
            examples=["/scan", "/scan dependencies"]
        ))
        self.register(Command(
            name="/secrets",
            description="Manage secrets",
            group=CommandGroup.SECURITY,
            usage="/secrets [action]",
            examples=["/secrets list", "/secrets add KEY value"]
        ))
        
        # Browser commands
        self.register(Command(
            name="/browser",
            description="Browser automation",
            group=CommandGroup.BROWSER,
            usage="/browser [action] [url]",
            examples=["/browser open https://google.com"]
        ))
        self.register(Command(
            name="/playwright",
            description="Playwright operations",
            group=CommandGroup.BROWSER,
            usage="/playwright [action]",
            examples=["/playwright screenshot", "/playwright test"]
        ))
        self.register(Command(
            name="/selenium",
            description="Selenium operations",
            group=CommandGroup.BROWSER,
            usage="/selenium [action]",
            examples=["/selenium test"]
        ))
        self.register(Command(
            name="/workflow",
            description="Workflow automation",
            group=CommandGroup.BROWSER,
            usage="/workflow [action]",
            examples=["/workflow create", "/workflow run"]
        ))
        self.register(Command(
            name="/automation",
            description="Automation operations",
            group=CommandGroup.BROWSER,
            usage="/automation [action]",
            examples=["/automation create", "/automation list"]
        ))
        
        # Memory commands
        self.register(Command(
            name="/save",
            description="Save to memory",
            group=CommandGroup.MEMORY,
            usage="/save [key] [value]",
            examples=["/save language python", "/save theme dark"]
        ))
        self.register(Command(
            name="/load",
            description="Load from memory",
            group=CommandGroup.MEMORY,
            usage="/load [key]",
            examples=["/load language"]
        ))
        self.register(Command(
            name="/forget",
            description="Forget from memory",
            group=CommandGroup.MEMORY,
            usage="/forget [key]",
            examples=["/forget language"]
        ))
        self.register(Command(
            name="/remember",
            description="Remember something",
            group=CommandGroup.MEMORY,
            usage="/remember [key] [value]",
            examples=["/remember password123 mypassword"]
        ))
        self.register(Command(
            name="/export-memory",
            description="Export memory",
            group=CommandGroup.MEMORY,
            usage="/export-memory [file]",
            examples=["/export-memory memory.json"]
        ))
        self.register(Command(
            name="/import-memory",
            description="Import memory",
            group=CommandGroup.MEMORY,
            usage="/import-memory [file]",
            examples=["/import-memory memory.json"]
        ))
        
        # Tools commands
        self.register(Command(
            name="/tool",
            description="Tool operations",
            group=CommandGroup.TOOLS,
            usage="/tool [action] [args]",
            examples=["/tool list", "/tool run calculator add 2 2"]
        ))
        self.register(Command(
            name="/install",
            description="Install tool or package",
            group=CommandGroup.TOOLS,
            usage="/install [package]",
            examples=["/install requests", "/install -g typescript"]
        ))
        self.register(Command(
            name="/uninstall",
            description="Uninstall tool or package",
            group=CommandGroup.TOOLS,
            usage="/uninstall [package]",
            examples=["/uninstall requests"]
        ))
        self.register(Command(
            name="/update",
            description="Update tool or package",
            group=CommandGroup.TOOLS,
            usage="/update [package]",
            examples=["/update", "/update requests"]
        ))
        self.register(Command(
            name="/list-tools",
            description="List installed tools",
            group=CommandGroup.TOOLS,
            usage="/list-tools",
            examples=["/list-tools"]
        ))
        
        # MCP commands
        self.register(Command(
            name="/mcp",
            description="MCP operations",
            group=CommandGroup.MCP,
            usage="/mcp [action] [args]",
            examples=["/mcp list", "/mcp connect server"]
        ))
        self.register(Command(
            name="/mcp-connect",
            description="Connect to MCP server",
            group=CommandGroup.MCP,
            usage="/mcp-connect [server]",
            examples=["/mcp-connect localhost:3000"]
        ))
        self.register(Command(
            name="/mcp-list",
            description="List MCP servers",
            group=CommandGroup.MCP,
            usage="/mcp-list",
            examples=["/mcp-list"]
        ))
        self.register(Command(
            name="/mcp-install",
            description="Install MCP server",
            group=CommandGroup.MCP,
            usage="/mcp-install [server]",
            examples=["/mcp-install @anthropic/mcp-server"]
        ))
        self.register(Command(
            name="/mcp-remove",
            description="Remove MCP server",
            group=CommandGroup.MCP,
            usage="/mcp-remove [server]",
            examples=["/mcp-remove @anthropic/mcp-server"]
        ))
        
        # Automation commands
        self.register(Command(
            name="/auto",
            description="Enable automatic mode",
            group=CommandGroup.AUTOMATION,
            usage="/auto [on|off]",
            examples=["/auto on", "/auto off"]
        ))
        self.register(Command(
            name="/manual",
            description="Enable manual mode",
            group=CommandGroup.AUTOMATION,
            usage="/manual",
            examples=["/manual"]
        ))
        self.register(Command(
            name="/safe",
            description="Enable safe mode",
            group=CommandGroup.AUTOMATION,
            usage="/safe [on|off]",
            examples=["/safe on"]
        ))
        self.register(Command(
            name="/full-auto",
            description="Enable full auto mode",
            group=CommandGroup.AUTOMATION,
            usage="/full-auto [on|off]",
            examples=["/full-auto on"]
        ))
        self.register(Command(
            name="/autonomous",
            description="Enable autonomous mode",
            group=CommandGroup.AUTOMATION,
            usage="/autonomous [on|off]",
            examples=["/autonomous on"]
        ))
        
        # Monitoring commands
        self.register(Command(
            name="/trace",
            description="View execution trace",
            group=CommandGroup.MONITORING,
            usage="/trace [session]",
            examples=["/trace", "/trace last"]
        ))
        self.register(Command(
            name="/profile",
            description="Profile execution",
            group=CommandGroup.MONITORING,
            usage="/profile [target]",
            examples=["/profile", "/profile main.py"]
        ))
        self.register(Command(
            name="/metrics",
            description="View metrics",
            group=CommandGroup.MONITORING,
            usage="/metrics [period]",
            examples=["/metrics", "/metrics today"]
        ))
        self.register(Command(
            name="/tokens",
            description="View token usage",
            group=CommandGroup.MONITORING,
            usage="/tokens",
            examples=["/tokens"]
        ))
        self.register(Command(
            name="/cost",
            description="View cost analysis",
            group=CommandGroup.MONITORING,
            usage="/cost [period]",
            examples=["/cost", "/cost today"]
        ))
        self.register(Command(
            name="/performance",
            description="View performance metrics",
            group=CommandGroup.MONITORING,
            usage="/performance",
            examples=["/performance"]
        ))
        
        # Advanced commands
        self.register(Command(
            name="/deep-research",
            description="Deep research on a topic",
            group=CommandGroup.ADVANCED,
            usage="/deep-research [topic]",
            examples=["/deep-research machine learning"]
        ))
        self.register(Command(
            name="/analyze-repo",
            description="Analyze repository",
            group=CommandGroup.ADVANCED,
            usage="/analyze-repo [repo]",
            examples=["/analyze-repo https://github.com/user/repo"]
        ))
        self.register(Command(
            name="/explain-codebase",
            description="Explain codebase",
            group=CommandGroup.ADVANCED,
            usage="/explain-codebase [path]",
            examples=["/explain-codebase src/"]
        ))
        self.register(Command(
            name="/index-project",
            description="Index project for search",
            group=CommandGroup.ADVANCED,
            usage="/index-project",
            examples=["/index-project"]
        ))
        self.register(Command(
            name="/search-symbol",
            description="Search for symbol",
            group=CommandGroup.ADVANCED,
            usage="/search-symbol [symbol]",
            examples=["/search-symbol main"]
        ))
        self.register(Command(
            name="/find-references",
            description="Find references to symbol",
            group=CommandGroup.ADVANCED,
            usage="/find-references [symbol]",
            examples=["/find-references main"]
        ))
        self.register(Command(
            name="/generate-tests",
            description="Generate tests",
            group=CommandGroup.ADVANCED,
            usage="/generate-tests [target]",
            examples=["/generate-tests", "/generate-tests src/"]
        ))
        self.register(Command(
            name="/fix-all",
            description="Fix all issues",
            group=CommandGroup.ADVANCED,
            usage="/fix-all",
            examples=["/fix-all"]
        ))
        self.register(Command(
            name="/review-pr",
            description="Review pull request",
            group=CommandGroup.ADVANCED,
            usage="/review-pr [pr]",
            examples=["/review-pr 123"]
        ))
        self.register(Command(
            name="/create-spec",
            description="Create specification",
            group=CommandGroup.ADVANCED,
            usage="/create-spec [topic]",
            examples=["/create-spec authentication"]
        ))
        self.register(Command(
            name="/create-roadmap",
            description="Create roadmap",
            group=CommandGroup.ADVANCED,
            usage="/create-roadmap [project]",
            examples=["/create-roadmap myproject"]
        ))
        self.register(Command(
            name="/design-system",
            description="Design system",
            group=CommandGroup.ADVANCED,
            usage="/design-system",
            examples=["/design-system"]
        ))
        self.register(Command(
            name="/run-ci",
            description="Run CI pipeline",
            group=CommandGroup.ADVANCED,
            usage="/run-ci",
            examples=["/run-ci"]
        ))
        self.register(Command(
            name="/deploy-preview",
            description="Deploy preview",
            group=CommandGroup.ADVANCED,
            usage="/deploy-preview",
            examples=["/deploy-preview"]
        ))
        self.register(Command(
            name="/benchmark-project",
            description="Benchmark project",
            group=CommandGroup.ADVANCED,
            usage="/benchmark-project",
            examples=["/benchmark-project"]
        ))
        self.register(Command(
            name="/profile-project",
            description="Profile project",
            group=CommandGroup.ADVANCED,
            usage="/profile-project",
            examples=["/profile-project"]
        ))
        self.register(Command(
            name="/scan-security",
            description="Scan security",
            group=CommandGroup.ADVANCED,
            usage="/scan-security",
            examples=["/scan-security"]
        ))
        self.register(Command(
            name="/migrate-project",
            description="Migrate project",
            group=CommandGroup.ADVANCED,
            usage="/migrate-project [target]",
            examples=["/migrate-project"]
        ))
        self.register(Command(
            name="/upgrade-dependencies",
            description="Upgrade dependencies",
            group=CommandGroup.ADVANCED,
            usage="/upgrade-dependencies",
            examples=["/upgrade-dependencies"]
        ))
        self.register(Command(
            name="/create-agent",
            description="Create custom agent",
            group=CommandGroup.ADVANCED,
            usage="/create-agent [name]",
            examples=["/create-agent myagent"]
        ))
        self.register(Command(
            name="/install-skill",
            description="Install skill",
            group=CommandGroup.ADVANCED,
            usage="/install-skill [skill]",
            examples=["/install-skill my-skill"]
        ))
    
    def register(self, command: Command):
        """Register a command"""
        self._commands[command.name] = command
        if command.group not in self._groups:
            self._groups[command.group] = []
        self._groups[command.group].append(command.name)
    
    def get(self, name: str) -> Optional[Command]:
        """Get command by name"""
        return self._commands.get(name)
    
    def list_all(self) -> list[Command]:
        """List all commands"""
        return list(self._commands.values())
    
    def list_by_group(self, group: CommandGroup) -> list[Command]:
        """List commands by group"""
        names = self._groups.get(group, [])
        return [self._commands[name] for name in names]
    
    def search(self, query: str) -> list[Command]:
        """Search commands by name or description"""
        query_lower = query.lower()
        results = []
        for cmd in self._commands.values():
            if query_lower in cmd.name.lower() or query_lower in cmd.description.lower():
                results.append(cmd)
        return results
    
    def parse(self, input_text: str) -> tuple[Optional[Command], str]:
        """Parse input text and extract command and arguments"""
        input_text = input_text.strip()
        if not input_text.startswith("/"):
            return None, input_text
        
        parts = input_text.split(maxsplit=1)
        cmd_name = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        # Try exact match first
        cmd = self.get(cmd_name)
        if cmd:
            return cmd, args
        
        # Try fuzzy match
        for name, command in self._commands.items():
            if name.startswith(cmd_name):
                return command, args
        
        return None, input_text
