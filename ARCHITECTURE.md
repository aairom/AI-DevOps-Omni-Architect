# 🏗️ AI-DevOps Omni-Architect v42 - Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Streamlit Web UI<br/>Port 8501]
    end

    subgraph "Application Core"
        MAIN[Main Application<br/>ai-devops-Omni-Architect_v42.py]
        CONFIG[Configuration Manager<br/>config.py]
        SESSION[Session State Manager]
    end

    subgraph "AI Provider Layer"
        FACTORY[AI Provider Factory]
        OLLAMA[Ollama Provider<br/>Local Models]
        GEMINI[Gemini Provider<br/>Google AI]
        WATSONX[WatsonX Provider<br/>IBM AI]
        OPENAI[OpenAI Provider<br/>GPT-4]
    end

    subgraph "Utility Services"
        SECURITY[Security Manager<br/>utils/security.py]
        CACHE[Cache Manager<br/>utils/cache_manager.py]
        GIT[Git Manager<br/>utils/git_manager.py]
    end

    subgraph "External Services"
        REDIS[(Redis Cache<br/>Optional)]
        GITREPO[Git Repository]
        FILESYSTEM[File System]
    end

    subgraph "Security Features"
        ENCRYPT[Credential Encryption]
        VALIDATE[Input Validation]
        SANITIZE[Command Sanitization]
        PATHCHECK[Path Traversal Protection]
    end

    UI --> MAIN
    MAIN --> CONFIG
    MAIN --> SESSION
    MAIN --> FACTORY
    
    FACTORY --> OLLAMA
    FACTORY --> GEMINI
    FACTORY --> WATSONX
    FACTORY --> OPENAI
    
    MAIN --> SECURITY
    MAIN --> CACHE
    MAIN --> GIT
    
    SECURITY --> ENCRYPT
    SECURITY --> VALIDATE
    SECURITY --> SANITIZE
    SECURITY --> PATHCHECK
    
    CACHE --> REDIS
    GIT --> GITREPO
    MAIN --> FILESYSTEM
    
    CONFIG -.->|Environment Variables| GEMINI
    CONFIG -.->|Environment Variables| WATSONX
    CONFIG -.->|Environment Variables| OPENAI

    style UI fill:#e1f5ff
    style MAIN fill:#fff3e0
    style FACTORY fill:#f3e5f5
    style SECURITY fill:#ffebee
    style CACHE fill:#e8f5e9
    style GIT fill:#fff9c4
```

## Component Flow Diagram

```mermaid
flowchart LR
    subgraph "Request Flow"
        A[User Request] --> B{Request Type}
        B -->|Infrastructure| C[IaC Generation]
        B -->|Observability| D[Monitoring Setup]
        B -->|Security| E[Security Hardening]
        B -->|Execution| F[Command Execution]
        B -->|Git| G[Version Control]
    end

    subgraph "Processing Pipeline"
        C --> H[Prompt Builder]
        D --> H
        E --> H
        H --> I{Check Cache}
        I -->|Hit| J[Return Cached]
        I -->|Miss| K[AI Provider]
        K --> L[Generate Response]
        L --> M[Cache Result]
        M --> N[Return to User]
        J --> N
    end

    subgraph "Security Layer"
        F --> O[Validate Command]
        O --> P[Sanitize Input]
        P --> Q[Execute Safely]
        Q --> R[Return Output]
    end

    subgraph "Git Operations"
        G --> S[Git Manager]
        S --> T{Operation}
        T -->|Status| U[Show Status]
        T -->|Commit| V[Create Commit]
        T -->|Push| W[Push Changes]
        T -->|Branch| X[Manage Branches]
    end

    style A fill:#e3f2fd
    style H fill:#fff3e0
    style I fill:#f3e5f5
    style K fill:#e1bee7
    style O fill:#ffcdd2
    style S fill:#fff9c4
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Main as Main App
    participant Cache as Cache Manager
    participant Security as Security Manager
    participant Provider as AI Provider
    participant External as External API

    User->>UI: Submit Request
    UI->>Main: Process Request
    Main->>Security: Validate Input
    Security-->>Main: Validated
    Main->>Cache: Check Cache
    
    alt Cache Hit
        Cache-->>Main: Return Cached Result
        Main-->>UI: Display Result
        UI-->>User: Show Output
    else Cache Miss
        Main->>Provider: Generate Request
        Provider->>Security: Encrypt API Key
        Security-->>Provider: Encrypted Key
        Provider->>External: API Call
        External-->>Provider: Response
        Provider-->>Main: Generated Content
        Main->>Cache: Store Result
        Main-->>UI: Display Result
        UI-->>User: Show Output
    end
```

## Module Dependency Graph

```mermaid
graph TD
    subgraph "Core Modules"
        MAIN[ai-devops-Omni-Architect_v42.py]
        CONFIG[config.py]
    end

    subgraph "Provider Modules"
        PROVIDER_INIT[providers/__init__.py]
        AI_PROVIDER[providers/ai_provider.py]
    end

    subgraph "Utility Modules"
        UTILS_INIT[utils/__init__.py]
        SECURITY[utils/security.py]
        CACHE[utils/cache_manager.py]
        GIT[utils/git_manager.py]
    end

    subgraph "Test Modules"
        TEST_INIT[tests/__init__.py]
        TEST_SEC[tests/test_security.py]
    end

    subgraph "External Dependencies"
        STREAMLIT[streamlit]
        OLLAMA[ollama]
        REQUESTS[requests]
        CRYPTOGRAPHY[cryptography]
        GITPYTHON[gitpython]
        REDIS_LIB[redis]
    end

    MAIN --> CONFIG
    MAIN --> PROVIDER_INIT
    MAIN --> UTILS_INIT
    MAIN --> STREAMLIT

    PROVIDER_INIT --> AI_PROVIDER
    AI_PROVIDER --> OLLAMA
    AI_PROVIDER --> REQUESTS

    UTILS_INIT --> SECURITY
    UTILS_INIT --> CACHE
    UTILS_INIT --> GIT

    SECURITY --> CRYPTOGRAPHY
    CACHE --> REDIS_LIB
    GIT --> GITPYTHON

    TEST_SEC --> SECURITY

    style MAIN fill:#ffeb3b
    style CONFIG fill:#4caf50
    style AI_PROVIDER fill:#2196f3
    style SECURITY fill:#f44336
    style CACHE fill:#00bcd4
    style GIT fill:#ff9800
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        INPUT[User Input]
        
        subgraph "Input Validation"
            VAL1[Type Validation]
            VAL2[Length Validation]
            VAL3[Format Validation]
        end
        
        subgraph "Path Security"
            PATH1[Path Normalization]
            PATH2[Traversal Detection]
            PATH3[Whitelist Check]
        end
        
        subgraph "Command Security"
            CMD1[Command Whitelist]
            CMD2[Argument Sanitization]
            CMD3[Shell Injection Prevention]
        end
        
        subgraph "Credential Security"
            CRED1[Encryption at Rest]
            CRED2[Secure Storage]
            CRED3[Key Rotation]
        end
        
        OUTPUT[Secure Execution]
    end

    INPUT --> VAL1
    VAL1 --> VAL2
    VAL2 --> VAL3
    VAL3 --> PATH1
    PATH1 --> PATH2
    PATH2 --> PATH3
    PATH3 --> CMD1
    CMD1 --> CMD2
    CMD2 --> CMD3
    CMD3 --> CRED1
    CRED1 --> CRED2
    CRED2 --> CRED3
    CRED3 --> OUTPUT

    style INPUT fill:#ffcdd2
    style OUTPUT fill:#c8e6c9
    style VAL1 fill:#fff9c4
    style PATH1 fill:#b3e5fc
    style CMD1 fill:#f8bbd0
    style CRED1 fill:#d1c4e9
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DEV[Local Development]
        VENV[Python Virtual Env]
        OLLAMA_LOCAL[Local Ollama]
    end

    subgraph "Production Options"
        subgraph "Docker Deployment"
            DOCKER[Docker Container]
            COMPOSE[Docker Compose]
        end
        
        subgraph "Cloud Deployment"
            K8S[Kubernetes]
            CLOUD[Cloud Platform]
        end
    end

    subgraph "External Services"
        REDIS_PROD[Redis Cache]
        GIT_REMOTE[Git Remote]
        AI_APIS[AI Provider APIs]
    end

    DEV --> VENV
    DEV --> OLLAMA_LOCAL
    
    VENV -.->|Build| DOCKER
    DOCKER --> COMPOSE
    COMPOSE -.->|Deploy| K8S
    K8S --> CLOUD
    
    DOCKER --> REDIS_PROD
    K8S --> REDIS_PROD
    
    CLOUD --> GIT_REMOTE
    CLOUD --> AI_APIS

    style DEV fill:#e1f5ff
    style DOCKER fill:#fff3e0
    style K8S fill:#f3e5f5
    style REDIS_PROD fill:#ffebee
```

## Cache Strategy

```mermaid
flowchart TD
    A[Request] --> B{Cache Enabled?}
    B -->|No| C[Direct AI Call]
    B -->|Yes| D{Check Memory Cache}
    
    D -->|Hit| E[Return from Memory]
    D -->|Miss| F{Redis Available?}
    
    F -->|Yes| G{Check Redis}
    F -->|No| C
    
    G -->|Hit| H[Return from Redis]
    G -->|Miss| C
    
    C --> I[AI Provider Response]
    I --> J[Store in Memory]
    J --> K{Redis Available?}
    K -->|Yes| L[Store in Redis]
    K -->|No| M[Return Response]
    L --> M

    style E fill:#c8e6c9
    style H fill:#c8e6c9
    style I fill:#fff9c4
    style J fill:#b3e5fc
    style L fill:#b3e5fc
```

---

## Key Components

### 1. **Main Application** (`ai-devops-Omni-Architect_v42.py`)
- Streamlit-based web interface
- Session state management
- Request routing and orchestration
- UI rendering and user interaction

### 2. **Configuration Manager** (`config.py`)
- Environment variable management
- Application constants
- Provider configurations
- Security settings

### 3. **AI Provider Layer** (`providers/ai_provider.py`)
- Abstract provider interface
- Multiple provider implementations
- Unified API for all providers
- Error handling and validation

### 4. **Security Manager** (`utils/security.py`)
- Credential encryption/decryption
- Input validation and sanitization
- Command whitelist enforcement
- Path traversal prevention

### 5. **Cache Manager** (`utils/cache_manager.py`)
- In-memory caching
- Optional Redis integration
- TTL-based expiration
- Cache statistics

### 6. **Git Manager** (`utils/git_manager.py`)
- Repository operations
- Commit management
- Branch operations
- Remote synchronization

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Streamlit |
| **Backend** | Python 3.9+ |
| **AI Providers** | Ollama, Gemini, WatsonX, OpenAI |
| **Caching** | In-Memory, Redis (optional) |
| **Security** | Cryptography, Input Validation |
| **Version Control** | GitPython |
| **Containerization** | Docker, Docker Compose |
| **Orchestration** | Kubernetes (optional) |

---

## Design Patterns

1. **Factory Pattern**: AI Provider creation
2. **Singleton Pattern**: Configuration and managers
3. **Strategy Pattern**: Different AI providers
4. **Decorator Pattern**: Caching layer
5. **Observer Pattern**: Session state management

---

**Built with ❤️ for DevOps Engineers and Platform Teams**