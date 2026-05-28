from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    app_name: str = "Flow DeepAgent"
    debug: bool = False
    log_level: str = "INFO"
    log_to_console: bool = True
    log_file: str = "app.log"
    log_max_bytes: int = 5 * 1024 * 1024
    log_backup_count: int = 5
    port: int


class WorkspaceDirs(BaseModel):
    artifacts: str = "artifacts"
    outputs: str = "outputs"
    temp: str = "temp"
    logs: str = "logs"


class WorkspaceConfig(BaseModel):
    root: str = "./workspace"
    dirs: WorkspaceDirs = Field(default_factory=WorkspaceDirs)


class MCPServer(BaseModel):
    name: str
    url: str
    enabled: bool = True


class MCPRuntimeConfig(BaseModel):
    timeout: int = 10
    retry_interval: int = 5
    health_check_interval: int = 30


class MCPConfig(BaseModel):
    runtime: MCPRuntimeConfig = Field(default_factory=MCPRuntimeConfig)
    servers: List[MCPServer] = Field(default_factory=list)


class ProviderConfig(BaseModel):
    base_url: str
    api_key_env: Optional[str] = None


class ProvidersConfig(BaseModel):
    dashscope: Optional[ProviderConfig] = None
    openai: Optional[ProviderConfig] = None
    ollama: Optional[ProviderConfig] = None
    cstcloud: Optional[ProviderConfig] = None


class LLMConfig(BaseModel):
    provider: str
    model: str
    temperature: float = 0


class PolicyConfig(BaseModel):
    deny_tools: List[str] = Field(default_factory=list)
    allow_tools: List[str] = Field(default_factory=list)
    total_call_budget: int = 100
    per_tool_budget: Dict[str, int] = Field(default_factory=dict)


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    name: str = "flow_agent"

class DefaultUserConfig(BaseModel):
    name: str
    password: str
    nickname: str


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    llm: LLMConfig = Field(
        default_factory=lambda: LLMConfig(
            provider="dashscope",
            model="qwen-max",
        )
    )
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    default_user: DefaultUserConfig = Field(default_factory=DefaultUserConfig)
