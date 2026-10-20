# MASS — Modular App Service Stack

**MASS (Modular App Service Stack)** is an architectural engine designed to compose, validate, and scaffold containerized, production-grade backend applications from modular plugins.
As generative coding and AI tools accelerate development, they frequently produce unmaintainable "AI slop"—disorganized, brittle monoliths filled with copy-pasted boilerplate, broken wiring, and zero architectural contracts.
MASS eliminates this chaos by enforcing strict capability contracts, automated dependency resolution, and declarative configuration, enabling developers and AI agents to reliably generate clean, modular, and containerized FastAPI services every single time.

---

## Developer Quickstart & Demo

### 1. Clone & Setup

Clone the repository and install the `mass` CLI in your local virtual environment:

```bash
git clone <repository-url>
cd mass-app-stack
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Verify the installation:

```bash
mass --help
```

---

### 2. Discover & Scaffold Plugins

MASS applications are assembled from **Plugins**. Plugins are either **container plugins** (e.g., databases, caches) that declare images, volumes, and outputs, or **code plugins** (e.g., authentication, API routes) that declare requirements, templates, and runtime dependencies.

```bash
# List all available plugins and their capabilities
mass plugins list

# Inspect a plugin's contracts, requirements, and config schema
mass plugins inspect postgres
mass plugins inspect authentication

# Scaffold a new custom code plugin
mass plugins create my-feature
```

Creating a plugin generates a `plugins/<name>/plugin.yaml` specification and starter route/service templates in `plugins/<name>/templates/`.

---

### 3. Generate Your Application

Developers can define and generate applications using two distinct approaches:

#### Approach 1: Declarative YAML Specification *(Recommended)*

The primary and recommended workflow is writing a clean YAML specification describing the desired application, ports, and plugin configurations.

1. **Write the application specification file** (e.g., `my-app.yaml`):

```yaml
name: movie-service
host_port: 8000

plugins:
  postgres:
    database: movies_db
    username: app_user
    password: ${POSTGRES_PASSWORD:-secretpassword}

  redis: {}

  authentication: {}

  welcome:
    message: "Welcome to the Movie Service API!"
```

2. **Validate the architecture** (checks contracts, missing dependencies, and schemas without writing code):

```bash
mass app validate my-app.yaml
```

3. **Build and scaffold the application**:

```bash
mass app build my-app.yaml
```

MASS resolves all inputs, outputs, and dependencies, rendering a completely self-contained project inside `generated/movie-service/` with its Dockerfile, `docker-compose.yml`, typed FastAPI routers, isolated `.env`, and database infrastructure.

---

#### Approach 2: REST API Endpoint

For automated pipelines, orchestrators, or web UI builders, MASS can generate applications via its control plane REST API.

1. **Start the MASS control plane server**:

```bash
uvicorn app.main:app --port 8000
```

2. **Send a generation request to the `/build` endpoint**:

```bash
curl -X POST http://localhost:8000/build \
  -H "Content-Type: application/json" \
  -d '{
    "application": {
      "name": "movie-service",
      "host_port": 8000
    },
    "plugins": {
      "postgres": {
        "database": "movies_db",
        "username": "app_user",
        "password": "secretpassword"
      },
      "redis": {},
      "authentication": {},
      "welcome": {
        "message": "Welcome to the Movie Service API!"
      }
    }
  }'
```

The application is validated and published directly into `generated/movie-service/`.

---

### 4. Run & Manage the Generated Application

MASS includes full runtime management for any generated application directly through the CLI:

```bash
# Start the application and its containers (e.g., FastAPI, PostgreSQL, Redis)
mass app run movie-service

# Check container status and HTTP reachability
mass app health movie-service

# View running container status
mass app status movie-service

# Stream logs from containers
mass app logs movie-service -f

# Generate and apply database migrations (SQLAlchemy & Alembic)
mass app makemigrations movie-service -m "initial schema"
mass app migrate movie-service

# Stop the application stack
mass app stop movie-service
```

---

## Conclusion

MASS shifts backend engineering away from fragile copy-paste generation and hallucinated AI slop toward disciplined, contract-driven architecture. By isolating services into reusable plugins and automating runtime wiring, it gives developers the flexibility to move fast without sacrificing code structure, safety, or maintainability. With MASS, building a production-ready microservice stack is as simple as defining what you need and letting the stack assemble itself.
