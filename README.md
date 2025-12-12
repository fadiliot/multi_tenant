# Multi-Tenant Organization Service (FastAPI + MongoDB)

## 🎯 Objective

This project implements a backend service using FastAPI (Python) and MongoDB to support the creation and management of organizations in a multi-tenant style architecture. The system utilizes a **Master Database** for global metadata and dynamically creates isolated **collections-per-tenant** for organization-specific data, providing strong logical data separation.

## 🏛️ System Architecture

The architecture follows a **Schema-per-Tenant (Collection-per-Tenant)** model within a single MongoDB instance.

* **Application Layer:** Built using **FastAPI** for high performance and asynchronous operation.
* **Database Layer:** A single MongoDB instance is used.
    * **Master Data:** Stored in two master collections (`organizations` and `admin_users`) for authentication and tenant routing.
    * **Tenant Data:** Each organization (tenant) is given its own dedicated collection (`org_<organization_name>`) within the same database, ensuring isolation and flexibility.



## 🚀 Setup and Run Instructions

### Prerequisites

1.  **Python 3.11+**
2.  **MongoDB Community Server** (running and accessible on mongodb://localhost:27017/)
3.  **Git**

### 1. Clone the Repository and Setup Environment

```bash
git clone [YOUR_GITHUB_REPOSITORY_LINK]
cd multi-tenant-api

python -m venv venv
source venv/bin/activate  # Use 'venv\Scripts\activate.bat' on Windows
