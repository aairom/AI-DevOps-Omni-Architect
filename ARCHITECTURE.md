# 🏗️ AI-DevOps Omni-Architect v43 - Architecture

## 🆕 Async Architecture Overview

v43 introduces asynchronous operations for improved performance and scalability.

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

## Async Architecture Diagram (v43)

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Streamlit Web UI<br/>Port 8501]
    end

    subgraph "Application Core"
        MAIN[Main Application v43<br/>ai-devops-Omni-Architect_v43.py]
        CONFIG[Configuration Manager<br/>config.py]
        SESSION[Session State Manager]
        ASYNC_CTRL[Async Controller]
    end

    subgraph "Async AI Provider Layer"
        ASYNC_FACTORY[Async AI Provider Factory]
        ASYNC_OLLAMA[Async Ollama Provider<br/>Concurrent Local Models]
        ASYNC_GEMINI[Async Gemini Provider<br/>Concurrent Google AI]
        ASYNC_WATSONX[Async WatsonX Provider<br/>Concurrent IBM AI]
        ASYNC_OPENAI[Async OpenAI Provider<br/>Concurrent GPT-4]
    end

    subgraph "Sync AI Provider Layer (Fallback)"
        FACTORY[AI Provider Factory]
        OLLAMA[Ollama Provider]
        GEMINI[Gemini Provider]
        WATSONX[WatsonX Provider]
        OPENAI[OpenAI Provider]
    end

    subgraph "Utility Services"
        SECURITY[Security Manager<br/>utils/security.py]
        ASYNC_CACHE[Async Cache Manager<br/>utils/async_cache_manager.py]
        CACHE[Cache Manager<br/>utils/cache_manager.py]
        ASYNC_HELPERS[Async Helpers<br/>utils/async_helpers.py]
        GIT[Git Manager<br/>utils/git_manager.py]
    end

    subgraph "External Services"
        REDIS[(Redis Cache<br/>Optional)]
        GITREPO[Git Repository]
        FILESYSTEM[File System]
    end

    UI --> MAIN
    MAIN --> CONFIG
    MAIN --> SESSION
    MAIN --> ASYNC_CTRL
    
    ASYNC_CTRL --> ASYNC_FACTORY
    ASYNC_CTRL --> FACTORY
    
    ASYNC_FACTORY --> ASYNC_OLLAMA
    ASYNC_FACTORY --> ASYNC_GEMINI
    ASYNC_FACTORY --> ASYNC_WATSONX
    ASYNC_FACTORY --> ASYNC_OPENAI
    
    FACTORY --> OLLAMA
    FACTORY --> GEMINI
    FACTORY --> WATSONX
    FACTORY --> OPENAI
    
    MAIN --> SECURITY
    MAIN --> ASYNC_CACHE
    MAIN --> CACHE
    MAIN --> ASYNC_HELPERS
    MAIN --> GIT
    
    ASYNC_CACHE --> REDIS
    CACHE --> REDIS
    GIT --> GITREPO
    MAIN --> FILESYSTEM
    
    CONFIG -.->|Environment Variables| ASYNC_GEMINI
    CONFIG -.->|Environment Variables| ASYNC_WATSONX
    CONFIG -.->|Environment Variables| ASYNC_OPENAI

    style UI fill:#e1f5ff
    style MAIN fill:#fff3e0
    style ASYNC_FACTORY fill:#c8e6c9
    style ASYNC_OLLAMA fill:#c8e6c9
    style ASYNC_GEMINI fill:#c8e6c9
    style ASYNC_WATSONX fill:#c8e6c9
    style ASYNC_OPENAI fill:#c8e6c9
    style ASYNC_CACHE fill:#b2dfdb
    style ASYNC_HELPERS fill:#b2dfdb
    style SECURITY fill:#ffebee
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

## Async Data Flow Architecture (v43)

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Main as Main App v43
    participant AsyncHelper as Async Helper
    participant AsyncCache as Async Cache
    participant Security as Security Manager
    participant AsyncProvider as Async AI Provider
    participant External as External API

    User->>UI: Submit Request
    UI->>Main: Process Request
    Main->>Security: Validate Input
    Security-->>Main: Validated
    
    alt Async Mode Enabled
        Main->>AsyncHelper: Run Async Operation
        AsyncHelper->>AsyncCache: Check Cache (Async)
        
        alt Cache Hit
            AsyncCache-->>AsyncHelper: Return Cached Result
            AsyncHelper-->>Main: Cached Response
        else Cache Miss
            AsyncHelper->>AsyncProvider: Generate Request (Async)
            AsyncProvider->>Security: Encrypt API Key
            Security-->>AsyncProvider: Encrypted Key
            
            par Concurrent API Calls
                AsyncProvider->>External: API Call 1
                AsyncProvider->>External: API Call 2
                AsyncProvider->>External: API Call 3
            end
            
            External-->>AsyncProvider: Responses
            AsyncProvider-->>AsyncHelper: Generated Content
            AsyncHelper->>AsyncCache: Store Result (Async)
            AsyncHelper-->>Main: Response
        end
        
        Main-->>UI: Display Result
        UI-->>User: Show Output
    else Sync Mode (Fallback)
        Note over Main,External: Falls back to v42 sync flow
    end
```

## Async Batch Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Main as Main App
    participant BatchProcessor as Batch Processor
    participant AsyncProvider as Async Provider
    participant API1 as API Endpoint 1
    participant API2 as API Endpoint 2
    participant API3 as API Endpoint 3

    User->>UI: Submit Batch Request
    UI->>Main: Process Multiple Items
    Main->>BatchProcessor: Create Batch Tasks
    
    BatchProcessor->>AsyncProvider: Initialize Semaphore (Max 3)
    
    par Concurrent Processing (Rate Limited)
        BatchProcessor->>AsyncProvider: Task 1
        AsyncProvider->>API1: Request 1
        BatchProcessor->>AsyncProvider: Task 2
        AsyncProvider->>API2: Request 2
        BatchProcessor->>AsyncProvider: Task 3
        AsyncProvider->>API3: Request 3
    end
    
    API1-->>AsyncProvider: Response 1
    API2-->>AsyncProvider: Response 2
    API3-->>AsyncProvider: Response 3
    
    AsyncProvider-->>BatchProcessor: All Results
    BatchProcessor-->>Main: Aggregated Results
    Main-->>UI: Display All Results
    UI-->>User: Show Batch Output
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

## Async Cache Strategy (v43)

```mermaid
flowchart TD
    A[Request] --> B{Async Mode?}
    B -->|No| SYNC[Use Sync Cache]
    B -->|Yes| C{Check Async Memory Cache}
    
    C -->|Hit| D[Return from Async Memory]
    C -->|Miss| E{Redis Available?}
    
    E -->|Yes| F{Check Async Redis}
    E -->|No| G[Async AI Call]
    
    F -->|Hit| H[Return from Async Redis]
    F -->|Miss| G
    
    G --> I[Async AI Provider Response]
    I --> J[Store in Async Memory]
    J --> K{Redis Available?}
    K -->|Yes| L[Store in Async Redis]
    K -->|No| M[Return Response]
    L --> M
    
    SYNC --> N[Sync Cache Flow]

    style D fill:#c8e6c9
    style H fill:#c8e6c9
    style I fill:#fff9c4
    style J fill:#b3e5fc
    style L fill:#b3e5fc
    style G fill:#ffccbc
```

## Async Concurrency Control

```mermaid
flowchart LR
    subgraph "Request Queue"
        R1[Request 1]
        R2[Request 2]
        R3[Request 3]
        R4[Request 4]
        R5[Request 5]
    end
    
    subgraph "Semaphore (Max 3)"
        S[Semaphore<br/>Available: 3]
    end
    
    subgraph "Active Processing"
        P1[Processing 1]
        P2[Processing 2]
        P3[Processing 3]
    end
    
    subgraph "Waiting"
        W1[Waiting 4]
        W2[Waiting 5]
    end
    
    R1 --> S
    R2 --> S
    R3 --> S
    R4 --> W1
    R5 --> W2
    
    S --> P1
    S --> P2
    S --> P3
    
    P1 -.->|Complete| S
    P2 -.->|Complete| S
    P3 -.->|Complete| S
    
    W1 -.->|Acquire| S
    W2 -.->|Acquire| S
    
    style S fill:#fff9c4
    style P1 fill:#c8e6c9
    style P2 fill:#c8e6c9
    style P3 fill:#c8e6c9
    style W1 fill:#ffccbc
    style W2 fill:#ffccbc
```

---

## Key Components

### 1. **Main Applications**
- **v43 (Async)** (`ai-devops-Omni-Architect_v43.py`)
  - Async-first architecture
  - Concurrent AI operations
  - Batch processing support
  - Toggle between async/sync modes
  - Enhanced performance monitoring

- **v42 (Stable)** (`ai-devops-Omni-Architect_v42.py`)
- Streamlit-based web interface
- Session state management
- Request routing and orchestration
- UI rendering and user interaction

### 2. **Configuration Manager** (`config.py`)
- Environment variable management
- Application constants
- Provider configurations
- Security settings

### 3. **AI Provider Layers**
- **Async Providers** (`providers/async_ai_provider.py`) ⚡ NEW!
  - Async abstract provider interface
  - Concurrent request handling
  - Batch generation support
  - Non-blocking operations
  - Token caching for watsonx
  - Thread pool for CPU-bound operations

- **Sync Providers** (`providers/ai_provider.py`)
  - Abstract provider interface
  - Multiple provider implementations
  - Unified API for all providers
  - Error handling and validation

### 4. **Security Manager** (`utils/security.py`)
- Credential encryption/decryption
- Input validation and sanitization
- Command whitelist enforcement
- Path traversal prevention

### 5. **Cache Managers**
- **Async Cache Manager** (`utils/async_cache_manager.py`) ⚡ NEW!
  - Async in-memory caching
  - Async Redis integration
  - Concurrent cache operations
  - Batch get/set operations
  - Async lock management
  - Non-blocking cache access

- **Sync Cache Manager** (`utils/cache_manager.py`)
  - In-memory caching
  - Optional Redis integration
  - TTL-based expiration
  - Cache statistics

### 6. **Async Helpers** (`utils/async_helpers.py`) ⚡ NEW!
- Event loop management for Streamlit
- Async-to-sync decorators
- Batch processing utilities
- Progress tracking for async operations
- Retry logic with exponential backoff
- Semaphore-based concurrency control

### 7. **Git Manager** (`utils/git_manager.py`)
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
| **Async Runtime** | asyncio, aiohttp |
| **AI Providers** | Ollama, Gemini, WatsonX, OpenAI |
| **Caching** | In-Memory, Redis (optional), Async Redis |
| **Security** | Cryptography, Input Validation |
| **Version Control** | GitPython |
| **Containerization** | Docker, Docker Compose |
| **Orchestration** | Kubernetes (optional) |

---

## Design Patterns

1. **Factory Pattern**: AI Provider creation (sync & async)
2. **Singleton Pattern**: Configuration and managers
3. **Strategy Pattern**: Different AI providers
4. **Decorator Pattern**: Caching layer
5. **Observer Pattern**: Session state management
6. **Async/Await Pattern**: Non-blocking operations
7. **Semaphore Pattern**: Concurrency control
8. **Thread Pool Pattern**: CPU-bound async operations

---

**Built with ❤️ for DevOps Engineers and Platform Teams**