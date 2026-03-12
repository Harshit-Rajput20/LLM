# System Architecture

The system follows a microservice architecture.

User Request Flow:

User
→ API Gateway
→ RAG Service
→ Prompt Builder
→ LLM Client
→ Response Processor
→ User

Additional services will be added later.

Full architecture diagram:

```mermaid
 flowchart TB

%% ----------------------
%% CLIENT LAYER
%% ----------------------

subgraph Client Layer
A[User Browser / Mobile App]
A1[WebSocket / HTTP Streaming Client]
end

A --> A1

%% ----------------------
%% EDGE / ENTRY LAYER
%% ----------------------

subgraph Edge Layer
B[Load Balancer]
C[API Gateway]
end

A1 --> B
B --> C

%% ----------------------
%% AUTHENTICATION SERVICE
%% ----------------------

subgraph Authentication Microservice
D[Auth Service]
D1[(Users Table)]
D2[(Sessions Table)]
end

C --> D
D --> D1
D --> D2

%% ----------------------
%% CHAT SERVICE
%% ----------------------

subgraph Chat Gateway Service
E[Chat API Service]
E1[Request Validator]
E2[Rate Limiter]
E3[Request Tracker]
end

C --> E
E --> E1
E1 --> E2
E2 --> E3

%% ----------------------
%% DATABASE STORAGE
%% ----------------------

subgraph Database Layer
F[(Conversations Table)]
G[(Messages Table)]
H[(Analytics / Token Usage)]
end

E3 --> F
E3 --> G

%% ----------------------
%% QUEUE SYSTEM
%% ----------------------

subgraph Async Processing
I[Message Queue\nKafka / Redis / RabbitMQ]
end

E3 --> I

%% ----------------------
%% WORKER CLUSTER
%% ----------------------

subgraph LLM Worker Cluster
J[Worker Instance 1]
K[Worker Instance 2]
L[Worker Instance N]
end

I --> J
I --> K
I --> L

%% ----------------------
%% CONTEXT BUILDER
%% ----------------------

subgraph Context Manager
M[Conversation History Loader]
N[Context Window Manager]
end

J --> M
K --> M
L --> M

M --> G
M --> N

%% ----------------------
%% RAG PIPELINE
%% ----------------------

subgraph RAG Pipeline
O[Embedding Generator]
P[Vector Search]
Q[Knowledge Retrieval]
end

N --> O
O --> P
P --> Q

%% Vector DB

subgraph Vector Database
R[(Vector DB\nPinecone / Weaviate)]
end

P --> R

%% ----------------------
%% PROMPT BUILDER
%% ----------------------

subgraph Prompt Construction
S[Prompt Builder]
end

Q --> S
N --> S

%% ----------------------
%% LLM API
%% ----------------------

subgraph LLM Provider
T[LLM API]
end

S --> T

%% ----------------------
%% STREAMING RESPONSE
%% ----------------------

subgraph Response Processing
U[Token Stream Handler]
V[Response Assembler]
end

T --> U
U --> V

%% ----------------------
%% STORE RESPONSE
%% ----------------------

V --> G
V --> H

%% ----------------------
%% STREAM BACK TO USER
%% ----------------------

subgraph Realtime Delivery
W[WebSocket Streamer]
end

V --> W
W --> A1

%% ----------------------
%% OBSERVABILITY
%% ----------------------

subgraph Monitoring & Observability
X[Metrics Collector]
Y[Logging System]
Z[Tracing System]
end

E --> X
J --> X
K --> X
L --> X

E --> Y
J --> Y

E --> Z
J --> Z