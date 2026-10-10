# MASS - Modular Application Service Stack

**MASS** is a tool that builds complete backend applications from reusable building blocks called **Plugins**. 

Instead of writing repetitive boilerplate code to connect databases, caches, and APIs, you just tell MASS which plugins you want to use. It automatically figures out how they connect, writes the necessary code, and sets up your Docker infrastructure so the app is instantly ready to run.

---

## 🏗 Simple Architecture Overview

MASS works like an assembly line with three main stages:

### 1. Plugins (The Building Blocks)
Plugins are the features you want in your app. There are two types:
* **Container Plugins**: Infrastructure pieces like PostgreSQL or Redis.
* **Code Plugins**: Application features like Authentication, which generate actual Python code.

Each plugin has a blueprint (`plugin.yaml`) that says what it *provides* (e.g., "I am a database") and what it *requires* (e.g., "I need a database to work").

### 2. Resolvers (The Brains)
When you ask MASS to build an app, it sends your request through a series of "Resolvers". These are smart scripts that:
* Check your configuration for errors.
* Connect the dots (e.g., wiring the Authentication plugin to the PostgreSQL plugin).
* Safely handle sensitive secrets (like passwords) so they never leak into the code.

### 3. Generators (The Builders)
Once the Resolvers finish the blueprint, the "Generators" do the hard work of building it:
* They write the Python code for your new FastAPI app.
* They create a `docker-compose.yml` file to run your infrastructure.
* They generate a secure `.env` file to hold your passwords.

## 🎯 The Result
You get a complete folder inside the `generated/` directory containing a fully wired, production-like FastAPI app that you can instantly start with a single `docker compose up` command.
