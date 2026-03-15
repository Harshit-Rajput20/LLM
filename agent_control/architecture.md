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
%% EDGE LAYER
%% ----------------------

subgraph Edge Layer
B[Load Balancer]
C[API Gateway]
end

A1 --> B
B --> C

%% ----------------------
%% AUTH SERVICE
%% ----------------------

subgraph Authentication Service
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
E[Chat API]
E1[Request Validator]
E2[Rate Limiter]
E3[Request Tracker]
end

C --> E
E --> E1
E1 --> E2
E2 --> E3

%% ----------------------
%% QUIZ SERVICE
%% ----------------------

subgraph Quiz Generation Service
Q1[Quiz API]
Q2[Quiz Validator]
Q3[Quiz Job Creator]
end

C --> Q1
Q1 --> Q2
Q2 --> Q3

%% ----------------------
%% DATABASES
%% ----------------------

subgraph Database Layer
F[(Conversations)]
G[(Messages)]
H[(Analytics)]
QDB[(Quiz Table)]
QQ[(Quiz Questions)]
META[(Document Metadata DB)]
end

E3 --> F
E3 --> G
Q3 --> QDB

%% ----------------------
%% QUEUE
%% ----------------------

subgraph Async Queue
I[Kafka / Redis / RabbitMQ]
end

E3 --> I
Q3 --> I

%% ----------------------
%% WORKERS
%% ----------------------

subgraph Worker Cluster
J[Worker 1]
K[Worker 2]
L[Worker N]
end

I --> J
I --> K
I --> L

%% ----------------------
%% CONTEXT MANAGER
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
%% RAG INGESTION PIPELINE
%% ----------------------

subgraph RAG Ingestion Pipeline
RI1[Document Parser]
RI2[Document Cleaner]
RI3[Semantic Chunker]
RI4[Metadata Extractor]
RI5[Embedding Generator]
end

RI1 --> RI2
RI2 --> RI3
RI3 --> RI4
RI4 --> RI5

%% ----------------------
%% RAG STORAGE
%% ----------------------

subgraph RAG Storage Layer
DOC[(Document Storage\nS3 / MinIO)]
VDB[(Vector Database\nFAISS / Qdrant / Pinecone)]
KDB[(Keyword Index\nElasticsearch)]
end

RI3 --> DOC
RI4 --> META
RI5 --> VDB
RI4 --> KDB

%% ----------------------
%% RAG RETRIEVAL PIPELINE
%% ----------------------

subgraph RAG Retrieval Pipeline
RR1[Query Processor]
RR2[Query Expansion]
RR3[Hybrid Retrieval]

RR4[Vector Search]
RR5[Keyword Search]

RR6[Candidate Merger]
RR7[Reranker Model]
RR8[Context Builder]
end

N --> RR1
RR1 --> RR2
RR2 --> RR3

RR3 --> RR4
RR3 --> RR5

RR4 --> VDB
RR5 --> KDB

RR4 --> RR6
RR5 --> RR6

RR6 --> RR7
RR7 --> RR8

%% ----------------------
%% PROMPT BUILDER
%% ----------------------

subgraph Prompt Construction
S[Prompt Builder]
SQ[Quiz Prompt Builder]
end

RR8 --> S
RR8 --> SQ

%% ----------------------
%% LLM PROVIDER
%% ----------------------

subgraph LLM Provider
T[LLM API]
end

S --> T
SQ --> T

%% ----------------------
%% CHAT RESPONSE
%% ----------------------

subgraph Chat Response
U[Token Stream Handler]
V[Response Assembler]
end

T --> U
U --> V

%% ----------------------
%% QUIZ PIPELINE
%% ----------------------

subgraph Quiz Pipeline
QW[Quiz Generator]
QF[Quiz Formatter]
QP[PDF Generator]
end

T --> QW
QW --> QF
QF --> QP

%% ----------------------
%% QUIZ STORAGE
%% ----------------------

subgraph Quiz Storage
QS[(PDF Storage)]
end

QF --> QQ
QP --> QS
QP --> QDB

%% ----------------------
%% DELIVERY
%% ----------------------

subgraph Realtime Delivery
W[WebSocket Streamer]
end

V --> W
W --> A1

subgraph Quiz Delivery
QD[Quiz Download API]
end

QS --> QD
QD --> A1

%% ----------------------
%% OBSERVABILITY
%% ----------------------

subgraph Monitoring
X[Metrics]
Y[Logs]
Z[Tracing]
end

E --> X
J --> X
K --> X
L --> X

E --> Y
J --> Y

E --> Z
J --> Z