# MASS — Modular Application Service Stack

**Build backend application foundations from reusable plugins. Validate dependencies, generate code, and run the resulting stack with Docker Compose.**

MASS is a Python-based, plugin-driven application composition platform that automates the repetitive work involved in assembling backend applications.

Instead of manually wiring infrastructure services, managing plugin dependencies, creating boilerplate code, and writing Docker Compose configurations, developers define an application in a YAML specification. MASS validates the specification, resolves plugin dependencies and contracts, generates the application structure, and prepares the infrastructure required to run it.

The goal is to make backend application assembly **modular, repeatable, validated, and easier to maintain**.

---

## Table of Contents

- [1. The Problem MASS Solves](#1-the-problem-mass-solves)
- [2. Core Capabilities](#2-core-capabilities)
- [3. Architecture Overview](#3-architecture-overview)
- [4. Plugin System](#4-plugin-system)
- [5. Validation and Resolution Pipeline](#5-validation-and-resolution-pipeline)
- [6. Application Specifications](#6-application-specifications)
- [7. Command-Line Interface](#7-command-line-interface)
- [8. Application Generation](#8-application-generation)
- [9. Docker and Runtime Management](#9-docker-and-runtime-management)
- [10. Configuration and Secret Handling](#10-configuration-and-secret-handling)
- [11. REST API](#11-rest-api)
- [12. Project Structure](#12-project-structure)
- [13. Installation and Setup](#13-installation-and-setup)
- [14. Testing](#14-testing)

---

## 1. The Problem MASS Solves

Building a backend application involves more than writing business logic. Even a relatively small project often requires developers to:

- Configure databases and caching services.
- Connect application components through configuration and dependencies.
- Validate environment-specific settings.
- Manage secrets and environment variables.
- Generate application boilerplate.
- Configure containers, networking, ports, and persistent volumes.
- Coordinate multiple infrastructure services.
- Handle invalid configurations and partial build failures.

These tasks are frequently repeated across projects.

MASS introduces a reusable plugin system and an application composition pipeline to automate much of this setup.

Instead of manually assembling each application, a developer specifies the required plugins and their configuration. MASS determines how the selected components fit together and generates an application scaffold and its supporting infrastructure configuration.

**Example:** A developer can describe an application that uses PostgreSQL, Redis, and an authentication plugin without manually defining the dependency relationships between those plugins in Docker Compose.

---

## 2. Core Capabilities

| Capability | Description |
|---|---|
| Plugin registry | Discovers and inspects available plugins and their metadata. |
| Plugin validation | Checks plugin manifests against the expected schema and conventions. |
| Configuration validation | Validates configuration keys, required values, defaults, and types. |
| Dependency resolution | Resolves required capabilities to selected plugin providers. |
| Contract validation | Checks plugin input/output references and their declared types. |
| Application specifications | Defines applications declaratively using YAML. |
| Environment-variable resolution | Resolves `${VARIABLE_NAME}` references from the environment during specification loading. |
| Code generation | Generates application files and includes selected code plugins. |
| Infrastructure generation | Creates Docker Compose configuration for selected container plugins and the generated application. |
| Secret-file handling | Writes resolved secret configuration to a generated `.env` file with restrictive file permissions. |
| Safe application publishing | Uses staging directories, a build lock, and atomic directory publication to protect the build process. |
| CLI workflow | Supports plugin inspection, application validation, building, running, and stopping. |
| REST API | Exposes application-building and plugin-inspection endpoints through FastAPI. |
| Automated testing | Includes unit and integration tests for validation, resolution, generation, and runtime management. |

---

## 3. Architecture Overview

MASS is organized around three main responsibilities: describing components, resolving their relationships, and generating an application from the resulting plan.

```text
              Application Specification
                       YAML
                        |
                        v
              Application Spec Loader
                        |
                        v
                 Plugin Registry
                        |
                        v
              Configuration Resolver
                        |
                        v
               Dependency Resolver
                        |
                        v
             Contract Validation
                        |
                        v
               Input / Output
                  Resolution
                        |
                        v
                   Generators
                   /       \
                  v         v
          FastAPI App    Docker Compose
                  \         /
                   v       v
                 Generated App
                        |
                        v
                 Docker Compose
                  Run / Stop
```

### 3.1 Plugins — reusable building blocks

Plugins describe infrastructure services and application-level functionality. Each plugin declares metadata such as its type, capabilities, dependencies, configuration schema, inputs, outputs, and runtime requirements.

### 3.2 Resolvers — validation and composition

Resolvers validate user configuration, determine which plugins satisfy required capabilities, verify contracts, and prepare the resolved data that generators consume.

### 3.3 Generators — application assembly

Generators turn the resolved application definition into files. They produce the application scaffold, include generated code plugins, construct Docker Compose services, and prepare runtime configuration.

The separation between these responsibilities is important: plugin metadata describes components, resolvers determine how they fit together, and generators produce the resulting application.

---

## 4. Plugin System

Plugins are the primary extension mechanism in MASS.

A plugin is a reusable component described by a manifest. The registry loads plugin definitions, validates them, and makes their metadata available to the composition pipeline.

### 4.1 Container plugins

Container plugins represent services that run as containers.

Current examples include:

- **PostgreSQL** — relational database infrastructure.
- **Redis** — caching and key-value infrastructure.
- **MySQL** — alternative relational database infrastructure.

Container plugin definitions can describe information such as:

- Container image and tag.
- Capabilities provided by the plugin.
- Required capabilities.
- Configuration fields.
- Environment-variable mappings.
- Port mappings.
- Persistent volumes.

MASS uses this metadata to generate corresponding Docker Compose services.

### 4.2 Code plugins

Code plugins contribute application-side code or functionality.

Current examples include:

- **Authentication** — an application-level plugin.
- **Hello** — a simple code-plugin example.

Code plugins are processed by the code-generation pipeline and incorporated into the generated application structure.

The presence of a code plugin in a generated project does not, by itself, mean that every associated production concern—such as complete authorization policies, migrations, operational monitoring, or deployment security—is implemented automatically.

### 4.3 Capabilities and requirements

Plugins declare capabilities they provide and capabilities they require.

For example, an authentication plugin can require:

- A database capability.
- A key-value store capability.

When PostgreSQL and Redis are selected alongside authentication, MASS can resolve the requirements to the appropriate providers.

This makes the composition process capability-driven rather than dependent on manually hardcoding every plugin relationship.

### 4.4 Typed inputs and outputs

Plugins can declare inputs and outputs, including their data types and references.

The contract validator checks that:

- Input references correspond to declared requirements.
- The required provider can be resolved.
- Referenced outputs exist.
- Input and output types are compatible.

This catches composition errors before application generation.

---

## 5. Validation and Resolution Pipeline

MASS validates an application before generating its files.

### 5.1 Plugin manifest validation

Plugin definitions are validated against the expected schema, including the supported `mass/v1` API version and consistency between a plugin's declared name and its directory.

### 5.2 Plugin conformance validation

Local conformance checks detect issues such as:

- Duplicate capability declarations.
- Duplicate requirements or runtime dependencies.
- Invalid configuration defaults.
- Incorrect default-value types.
- Invalid environment placeholders.
- Invalid input declarations.

### 5.3 Configuration resolution

The configuration resolver:

1. Rejects unknown configuration keys.
2. Applies declared default values.
3. Checks required configuration fields.
4. Validates values against their declared types.
5. Preserves resolved configuration for subsequent stages.

Supported configuration types include strings, integers, numbers, and booleans.

### 5.4 Dependency resolution

The dependency resolver determines which selected plugins provide the capabilities required by other selected plugins.

It detects errors such as:

- Missing capability providers.
- Ambiguous providers.
- Self-dependencies.
- Dependency cycles.

### 5.5 Contract validation

The contract validator checks that declared inputs and outputs connect correctly across the resolved plugin graph.

### 5.6 Input and output resolution

The output resolver prepares plugin outputs, while the input resolver connects resolved values to the corresponding consumers.

Together, these stages prepare the data needed by the generators.

---

## 6. Application Specifications

Applications are described declaratively using YAML.

### Example: `movie-api.yaml`

```yaml
name: movie-api
host_port: 8001

plugins:
  postgres:
    database: movies
    username: app
    password: ${POSTGRES_PASSWORD}

  redis: {}

  authentication: {}
```

This specification describes an application named `movie-api` with PostgreSQL, Redis, and authentication plugins.

The optional `host_port` field controls the host-side port used to access the generated application. The application listens on port `8000` inside its container.

If `host_port` is omitted, the default is `8000`.

### Specification loading

The application-specification loader:

- Reads the YAML file.
- Rejects malformed YAML.
- Validates the top-level specification structure.
- Checks the application name.
- Rejects undeclared top-level fields.
- Resolves supported environment-variable references.
- Produces a validated application specification.

Application names are restricted to letters, numbers, underscores, and hyphens.

### Environment variables

Set the required variable before validating or building:

```bash
export POSTGRES_PASSWORD='your-local-development-password'
```

Then validate:

```bash
python -m app.cli app validate movie-api.yaml
```

If a referenced environment variable is missing, specification loading fails with an error identifying the missing variable.

Use environment variables for credentials rather than committing actual passwords to the repository.

---

## 7. Command-Line Interface

MASS provides a CLI for working with plugins and generated applications.

The current entry point is:

```bash
python -m app.cli
```

### 7.1 List available plugins

```bash
python -m app.cli plugins list
```

Displays registered plugins, versions, types, and provided capabilities.

### 7.2 Inspect a plugin

```bash
python -m app.cli plugins inspect postgres
```

Displays plugin metadata, capabilities, requirements, configuration, inputs, and outputs.

### 7.3 Validate an application

```bash
python -m app.cli app validate movie-api.yaml
```

This validates the specification, resolves the selected plugins and their dependencies, and checks plugin contracts.

Validation does not generate application files.

Example output:

```text
Application 'movie-api' is valid.
Selected plugins: postgres, redis, authentication
Dependencies: {'postgres': {}, 'redis': {},
               'authentication': {
                   'database': 'postgres',
                   'key_value_store': 'redis'
               }}
No application files were generated.
```

### 7.4 Build an application

```bash
python -m app.cli app build movie-api.yaml
```

The build pipeline validates and prepares the application, generates its files and Docker Compose configuration, and publishes the result into the `generated/` directory.

Existing generated applications are not silently overwritten. Use a different application name when creating another build.

### 7.5 Run an application

```bash
python -m app.cli app run movie-api
```

This runs the equivalent of:

```bash
docker compose up -d --build
```

from the generated application's directory.

The command reports Docker Compose failures and attempts to clean up the application if startup fails.

### 7.6 Stop an application

```bash
python -m app.cli app stop movie-api
```

This runs:

```bash
docker compose down
```

for that generated application.

Named volumes are not removed by default, so persisted database data may remain after the containers and network are stopped.

### 7.7 Complete workflow

```bash
export POSTGRES_PASSWORD='your-local-development-password'

python -m app.cli plugins list
python -m app.cli app validate movie-api.yaml
python -m app.cli app build movie-api.yaml
python -m app.cli app run movie-api

curl http://localhost:8001/

python -m app.cli app stop movie-api
```

The port in the `curl` command must match the `host_port` specified in the application YAML.

---

## 8. Application Generation

Once validation and resolution succeed, MASS generates the application structure.

### Generated files

A generated application contains files such as:

```text
generated/
└── movie-api/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   └── ...
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    ├── .env
    └── .gitignore
```

The precise contents depend on the selected plugins.

### FastAPI scaffold

The application generator creates a Python application package and a FastAPI entry point.

The generated application currently exposes a basic root endpoint:

```python
@app.get("/")
def root():
    return {"message": "Generated application is running"}
```

It also prepares the Python dependencies required by the generated application and selected plugins.

### Dockerfile

The generated Dockerfile uses Python 3.12, installs the generated requirements, copies the application package, and starts the FastAPI application with Uvicorn.

### Requirements generation

The generated `requirements.txt` includes FastAPI, Uvicorn, and declared runtime dependencies.

### Safe publication

The existing build pipeline uses:

- A staging directory.
- A per-application build lock.
- Cleanup after generation failures.
- Publication by renaming the staging directory after successful generation.
- Duplicate-application protection.

This helps prevent incomplete builds from appearing as successfully published applications.

---

## 9. Docker and Runtime Management

MASS generates a Docker Compose configuration for the selected container plugins and the application container.

### Infrastructure services

The Compose generator uses plugin metadata to prepare services with their declared:

- Container images.
- Ports.
- Environment configuration.
- Persistent volumes.

It also derives application service dependencies from the resolved plugin relationships.

### Application service

The generated application service:

- Builds from the generated Dockerfile.
- Exposes the application on the configured host port.
- Listens on port `8000` inside the container.
- Uses the generated `.env` file.
- Declares its resolved service dependencies.

### Configurable host port

For example:

```yaml
name: movie-api
host_port: 8001
plugins:
  postgres:
    database: movies
    username: app
    password: ${POSTGRES_PASSWORD}
  redis: {}
  authentication: {}
```

The generated Compose configuration maps host port `8001` to container port `8000`.

This allows different applications to use different host ports, provided the selected ports are available.

### Runtime failure handling

If Docker Compose returns a nonzero exit code during startup, MASS reports the failure and attempts to bring down the same application's Compose project.

A successful `docker compose up -d` means the services were started; it does not guarantee that every service is healthy or that the application is ready to accept requests.

---

## 10. Configuration and Secret Handling

MASS distinguishes configuration values from the code generated for an application.

### Environment-variable resolution

Specifications support references such as:

```yaml
password: ${POSTGRES_PASSWORD}
```

The specification loader resolves the referenced environment variable before the configuration is passed into the application-building pipeline.

If the variable is missing, the specification cannot be loaded successfully.

---

## 11. REST API

MASS also exposes a FastAPI interface.

### Root endpoint

```http
GET /
```

Returns a message indicating that MASS is running.

### Build endpoint

```http
POST /build
Content-Type: application/json
```

Example request:

```json
{
  "application": {
    "name": "movie-api",
    "host_port": 8001
  },
  "plugins": {
    "postgres": {
      "database": "movies",
      "username": "app",
      "password": "local-development-password"
    },
    "redis": {},
    "authentication": {}
  }
}
```

The endpoint validates configuration and plugin relationships, resolves dependencies, and generates the application.

The API uses HTTP error responses for conditions such as unknown plugins, invalid configuration, duplicate applications, concurrent builds, and generation failures.

### Plugin listing

```http
GET /plugins
```

Returns the available plugins.

### Plugin inspection

```http
GET /plugins/{plugin_name}
```

Returns metadata for the requested plugin or a not-found response when the plugin does not exist.

The API can be run through an ASGI server such as Uvicorn, using the FastAPI application defined in `app/main.py`.

---

## 12. Project Structure

The main project components are organized as follows:

```text
MASS - Modular App Service Stack/
├── app/
│   ├── main.py
│   ├── cli.py
│   ├── models.py
│   ├── application_spec.py
│   ├── application_service.py
│   ├── application_generator.py
│   ├── code_plugin_generator.py
│   ├── compose_generator.py
│   ├── config_resolver.py
│   ├── dependency_resolver.py
│   ├── input_resolver.py
│   ├── output_resolver.py
│   ├── plugin_registry.py
│   ├── plugin_conformance_validator.py
│   ├── plugin_contract_validator.py
│   ├── runtime_dependency_resolver.py
│   ├── runtime_manager.py
│   └── build_lock.py
├── plugins/
│   ├── postgres/
│   ├── redis/
│   ├── mysql/
│   ├── hello/
│   └── authentication/
├── generated/
├── tests/
├── requirements.txt
├── pytest.ini
└── README.md
```

The exact contents of individual plugin directories and generated applications depend on their manifests and selected functionality.

### Main modules

| Module | Responsibility |
|---|---|
| `plugin_registry.py` | Discovers and loads plugin definitions. |
| `plugin_conformance_validator.py` | Checks plugin metadata against local conformance rules. |
| `config_resolver.py` | Validates and resolves plugin configuration. |
| `dependency_resolver.py` | Resolves required capabilities and detects dependency errors. |
| `plugin_contract_validator.py` | Validates connections between plugin inputs and outputs. |
| `input_resolver.py` | Resolves plugin input values. |
| `output_resolver.py` | Resolves declared plugin outputs. |
| `application_spec.py` | Loads YAML application specifications and resolves environment references. |
| `application_service.py` | Coordinates application preparation and plugin resolution. |
| `application_generator.py` | Generates the FastAPI scaffold, Dockerfile, and requirements. |
| `code_plugin_generator.py` | Generates files contributed by code plugins. |
| `compose_generator.py` | Produces Docker Compose configuration and the generated environment file. |
| `runtime_dependency_resolver.py` | Derives application runtime dependencies from resolved plugins. |
| `runtime_manager.py` | Starts and stops generated applications through Docker Compose. |
| `build_lock.py` | Prevents overlapping builds of the same application. |
| `main.py` | Exposes the FastAPI API and orchestrates application builds. |
| `cli.py` | Provides the command-line interface. |

---

## 13. Installation and Setup

### Prerequisites

- Python 3.12 or a compatible Python version supported by the project.
- `pip` and Python virtual environments.
- Docker Desktop or a working Docker Engine installation.
- Docker Compose v2, available through `docker compose`.
- Git, if cloning the repository.

### Set up the environment

Clone or open the repository, then create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Check Docker availability:

```bash
docker info
docker compose version
```

List the available plugins:

```bash
python -m app.cli plugins list
```

Validate an application specification:

```bash
export POSTGRES_PASSWORD='your-local-development-password'
python -m app.cli app validate movie-api.yaml
```

Build and run it:

```bash
python -m app.cli app build movie-api.yaml
python -m app.cli app run movie-api
```

Test the application:

```bash
curl http://localhost:8001/
```

Stop it when finished:

```bash
python -m app.cli app stop movie-api
```

The URL port must match the application's configured `host_port`.

---

## 14. Testing

MASS uses `pytest` for unit and integration testing.

The test suite covers the core composition pipeline and its failure cases.

### Areas covered

- Plugin manifest validation.
- Configuration resolution and type checking.
- Dependency resolution.
- Plugin contract validation.
- Output resolution.
- Template rendering.
- Docker Compose generation.
- Integration testing of application generation.
- Secret-handling behavior.
- Build conflicts and failure cleanup.
- CLI command dispatch and error handling.
- Runtime manager behavior, including missing applications, Docker failures, and startup cleanup.

### Run all tests

```bash
pytest -q
```

The current development checkpoint is **84 passing tests**, based on the latest confirmed test run before the most recent host-port integration checks. Re-run the full suite after subsequent changes to establish the latest count.

The runtime manager tests mock Docker subprocess calls where appropriate, allowing the error-handling logic to be tested without starting real containers.


---

## Conclusion

MASS aims to make backend application assembly more systematic.

By combining declarative specifications, reusable plugins, configuration validation, capability-based dependency resolution, contract checking, code generation, and Docker Compose runtime management, it reduces the manual work required to assemble a backend application foundation.

Its architecture separates the definition of components from the logic that validates and connects them, making the platform extensible as new plugins, validation rules, and runtime capabilities are introduced.

**MASS is an evolving application composition platform: it already validates, generates, and runs application foundations, with further work focused on richer generated functionality, operational reliability, and production deployment.**
