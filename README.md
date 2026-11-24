# Fleet Management System --- Frappe POC

> **Purpose:** A small, demonstrable Fleet Management System built
> entirely on the Frappe Framework and Desk.\
> **Audience:** Engineering leads, Frappe developers, solution
> architects and POC stakeholders.\
> **Status:** Proof of Concept (POC) --- not production-ready

------------------------------------------------------------------------

## 1. POC objectives

Build a working fleet operations workflow using native Frappe
capabilities rather than introducing a separate application backend or
frontend.

The POC should demonstrate that Frappe can provide:

-   Master-data management for vehicles, drivers and locations.
-   Vehicle allocation to a driver for a defined period.
-   Trip creation, dispatch, completion and cancellation.
-   Odometer and fuel/expense capture.
-   Vehicle maintenance logging and availability control.
-   Role-based access, workflow approvals, activity history and reports.
-   REST API access for a future mobile application or external
    integration.

### Explicitly out of scope

Do not expand the POC into a full transport-management or telematics
platform. The first iteration excludes live GPS tracking, route
optimisation, payroll, fuel-card integrations, FASTag integrations,
vendor procurement, accounting integration, driver mobile app,
preventive-maintenance prediction and multi-company inter-company
settlement.

These can be evaluated after the core workflow is validated.

------------------------------------------------------------------------

## 2. Recommended implementation approach

Use a **custom Frappe app** (for example, `fleet_management`) installed
on a supported Frappe site. Model the business domain with DocTypes and
use the framework's built-in capabilities wherever practical.

  -----------------------------------------------------------------------
  Concern                             POC implementation
  ----------------------------------- -----------------------------------
  User interface                      Frappe Desk forms, List Views,
                                      reports and workspace

  Domain model                        Custom DocTypes, Link fields, child
                                      tables and naming series

  Business rules                      DocType controller validations and
                                      lifecycle hooks

  State transitions                   Frappe Workflow for Trip and
                                      Maintenance Request

  Authorization                       Roles, DocType permissions, User
                                      Permissions and permission query
                                      conditions where required

  Persistence                         MariaDB via Frappe ORM; no direct
                                      SQL for normal CRUD

  Background work                     `frappe.enqueue` / scheduled jobs
                                      only for genuinely asynchronous
                                      tasks

  Integration                         Frappe REST API and whitelisted
                                      methods with explicit permission
                                      checks

  Audit                               Document Versioning,
                                      comments/timeline and standard
                                      creation/modification metadata

  Reporting                           Query Reports / Script Reports and
                                      Dashboard Charts

  Deployment                          Bench-managed app, site
                                      configuration, migrations and
                                      controlled releases
  -----------------------------------------------------------------------

**Design principle:** Keep the POC deliberately Frappe-native. Do not
add a separate microservice, custom SPA or external workflow engine
unless a demonstrated requirement cannot be met cleanly in Frappe.

------------------------------------------------------------------------

## 3. High-level architecture

``` mermaid
flowchart TB
    U[Operations User / Fleet Manager]
    A[Administrator]
    M[Future Mobile App / External Client]

    subgraph FRAPPE["Frappe Site"]
      subgraph UX["Presentation Layer"]
        D[Desk Forms and List Views]
        W[Workspace and Dashboards]
        R[Reports]
      end

      subgraph APP["Application Layer — fleet_management"]
        API[REST API / Whitelisted Methods]
        DOC[DocTypes and Document Controllers]
        WF[Workflows and State Transitions]
        VAL[Validations and Business Rules]
        JOB[Background Jobs / Scheduler]
        PERM[Roles and Permission Checks]
      end

      subgraph CORE["Frappe Framework Services"]
        ORM[Frappe ORM]
        AUTH[Authentication and Authorization]
        AUDIT[Timeline, Versioning and Activity]
        QUEUE[Background Job Queue]
      end
    end

    DB[(MariaDB)]
    REDIS[(Redis Cache / Queue)]
    FILES[(File Storage)]

    U --> D
    U --> W
    U --> R
    A --> D
    M --> API

    D --> DOC
    W --> DOC
    R --> ORM
    API --> AUTH
    API --> PERM
    API --> DOC
    DOC --> WF
    DOC --> VAL
    DOC --> PERM
    DOC --> ORM
    DOC --> AUDIT
    JOB --> QUEUE
    QUEUE --> REDIS
    JOB --> DOC
    ORM --> DB
    AUDIT --> DB
    DOC --> FILES
```

### Architecture notes

1.  **Presentation:** Use Desk as the primary POC interface. Configure
    Workspace shortcuts, List Views, dashboards and reports for
    operational users.
2.  **Application:** Put validations in DocType controllers so they
    apply to Desk, REST API and background execution paths. Use
    whitelisted methods only for operations that need a purpose-built
    API.
3.  **Workflow:** Use Frappe Workflow for user-driven state transitions
    and role-based approval. Do not rely on a client script to enforce a
    business rule.
4.  **Persistence:** Use the Frappe ORM (`frappe.get_doc`,
    `frappe.new_doc`, `frappe.db.get_value`, etc.). Avoid direct
    database writes and raw SQL unless a reviewed reporting/query use
    case justifies it.
5.  **Security:** UI visibility is not authorization. Enforce access
    using DocType permissions, document-level permission logic and
    server-side checks.
6.  **Async processing:** Use background jobs for non-interactive work;
    do not enqueue simple validations or operations that must finish
    before a document can be saved.

------------------------------------------------------------------------

## 4. Functional scope and demo flow

The POC should support the following end-to-end scenario:

1.  Fleet Admin creates a vehicle and assigns it an active status.
2.  Fleet Admin creates a driver record and records licence validity.
3.  Dispatcher creates a trip, selecting a vehicle, driver, origin,
    destination and planned dates.
4.  On submission, server-side validation checks that the vehicle and
    driver are eligible and do not have overlapping active trips.
5.  Dispatcher submits the trip for approval. An authorised Fleet
    Manager approves or rejects it.
6.  On dispatch, the trip records the opening odometer. On completion,
    the closing odometer and actual end time are captured.
7.  The system calculates distance travelled and records trip expenses.
8.  If a vehicle requires repair, a Maintenance Request is created and
    the vehicle is marked unavailable for new trips until released.
9.  Fleet Manager reviews operational reports: active trips, vehicle
    utilisation, maintenance due and trip costs.

### Suggested demo data

-   3 vehicles: one available, one on an active trip, one under
    maintenance.
-   4 drivers: three active and one with an expired licence.
-   3 locations: Depot, Customer Site A and Customer Site B.
-   5 trips: Draft, Pending Approval, Approved, In Progress and
    Completed.
-   2 maintenance records: one Open and one Completed.

Use fictional data only. Do not load real driver licence numbers,
personal phone numbers or vehicle documents into a demo site.

------------------------------------------------------------------------

## 5. Domain model and DocTypes

Use the following DocTypes as the initial model. Keep the first POC
intentionally small; add fields only when a workflow or report needs
them.

### 5.1 Master DocTypes

#### Vehicle

  -------------------------------------------------------------------------
  Field                     Type                    Notes
  ------------------------- ----------------------- -----------------------
  `vehicle_name`            Data                    Human-readable label

  `registration_number`     Data, Unique            Normalised
                                                    registration; unique
                                                    constraint/validation

  `vehicle_type`            Link / Select           E.g. Car, Van, Truck

  `make`                    Data                    Manufacturer

  `model`                   Data                    Model

  `manufacturing_year`      Int                     Optional

  `capacity`                Float                   Define unit
                                                    consistently

  `fuel_type`               Select                  Petrol, Diesel, CNG,
                                                    EV, Other

  `current_odometer`        Float                   Latest verified
                                                    odometer reading

  `status`                  Select                  Available, On Trip,
                                                    Maintenance, Inactive

  `last_service_date`       Date                    Optional

  `next_service_due_date`   Date                    Optional
  -------------------------------------------------------------------------

**Naming:** `VEH-.YYYY.-.#####` or another agreed naming series.\
**Validation:** Registration number must be unique after normalisation.
Odometer cannot be negative. A vehicle in Maintenance or Inactive status
cannot be dispatched.

#### Driver

  Field                   Type         Notes
  ----------------------- ------------ ----------------------------------------
  `driver_name`           Data         Required
  `employee_id`           Data         Unique if sourced from HR
  `phone`                 Phone        Restrict access to appropriate roles
  `license_number`        Data         Treat as sensitive personal data
  `license_expiry_date`   Date         Required for dispatch eligibility
  `status`                Select       Active, Inactive, Suspended
  `notes`                 Small Text   Avoid sensitive or unnecessary details

**Validation:** Driver must be Active and licence must be valid on the
planned trip date. Do not expose licence data to general users or
include it in broad reports.

#### Fleet Location

  Field             Type           Notes
  ----------------- -------------- -----------------------------------------
  `location_name`   Data           Required
  `location_code`   Data, Unique   Stable reference
  `address`         Small Text     Optional
  `is_active`       Check          Prevent selection of inactive locations

### 5.2 Transaction DocTypes

#### Trip

  ---------------------------------------------------------------------------
  Field                   Type                    Notes
  ----------------------- ----------------------- ---------------------------
  `trip_id`               Naming Series           e.g. `TRIP-.YYYY.-.#####`

  `vehicle`               Link → Vehicle          Required

  `driver`                Link → Driver           Required

  `origin`                Link → Fleet Location   Required

  `destination`           Link → Fleet Location   Required

  `planned_start`         Datetime                Required

  `planned_end`           Datetime                Required

  `actual_start`          Datetime                Set on dispatch

  `actual_end`            Datetime                Set on completion

  `opening_odometer`      Float                   Captured at dispatch

  `closing_odometer`      Float                   Captured at completion

  `distance_travelled`    Float                   Derived server-side

  `purpose`               Small Text              Business reason

  `status`                Workflow State          Draft, Pending Approval,
                                                  Approved, In Progress,
                                                  Completed, Rejected,
                                                  Cancelled

  `trip_expenses`         Table → Trip Expense    Child table

  `remarks`               Text                    Optional
  ---------------------------------------------------------------------------

#### Trip Expense (Child Table)

  Field            Type       Notes
  ---------------- ---------- ----------------------------
  `expense_type`   Select     Fuel, Toll, Parking, Other
  `amount`         Currency   Must be non-negative
  `expense_date`   Date       Required
  `reference`      Data       Receipt/reference number
  `attachment`     Attach     Optional receipt

Do not store payment-card details. For the POC, expense capture is
informational and is not an accounting posting.

#### Maintenance Request

  -----------------------------------------------------------------------
  Field                   Type                    Notes
  ----------------------- ----------------------- -----------------------
  `vehicle`               Link → Vehicle          Required

  `reported_on`           Datetime                Default current time

  `issue_type`            Select                  Scheduled Service,
                                                  Breakdown, Inspection,
                                                  Other

  `description`           Text Editor / Small     Required
                          Text                    

  `priority`              Select                  Low, Medium, High,
                                                  Critical

  `odometer_reading`      Float                   Must not be less than
                                                  last verified reading

  `status`                Workflow State          Open, In Progress,
                                                  Completed, Cancelled

  `service_date`          Date                    Optional

  `cost`                  Currency                Optional POC value

  `resolution_notes`      Text                    Required on completion
  -----------------------------------------------------------------------

### 5.3 Relationships

``` mermaid
erDiagram
    VEHICLE ||--o{ TRIP : assigned_to
    DRIVER ||--o{ TRIP : drives
    FLEET_LOCATION ||--o{ TRIP : origin
    FLEET_LOCATION ||--o{ TRIP : destination
    TRIP ||--o{ TRIP_EXPENSE : contains
    VEHICLE ||--o{ MAINTENANCE_REQUEST : has
```

The diagram shows logical relationships. In Frappe, implement these with
Link fields and child tables; do not create a separate SQL schema
manually.

------------------------------------------------------------------------

## 6. Workflow and business rules

### 6.1 Trip lifecycle

``` mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> PendingApproval: Submit
    PendingApproval --> Approved: Approve
    PendingApproval --> Rejected: Reject
    Rejected --> Draft: Amend and resubmit
    Approved --> InProgress: Dispatch
    InProgress --> Completed: Complete trip
    Draft --> Cancelled: Cancel
    PendingApproval --> Cancelled: Cancel
    Approved --> Cancelled: Cancel before dispatch
    Completed --> [*]
    Cancelled --> [*]
```

Configure the exact state transitions and permitted roles in Frappe
Workflow. The POC may use `docstatus` for draft/submitted/cancelled
document lifecycle, but do not confuse `docstatus` with a business
workflow state. Decide whether Trip is submittable and keep the workflow
design consistent.

### 6.2 Required server-side validations

Implement and test these rules in the relevant DocType controller:

-   Vehicle and driver must be active.
-   Driver licence must be valid through the planned trip date.
-   Vehicle must not be Inactive or in Maintenance at dispatch.
-   No overlapping non-cancelled trips for the same vehicle.
-   No overlapping non-cancelled trips for the same driver.
-   Planned end must be later than planned start.
-   Origin and destination must differ unless the use case explicitly
    permits a local/round trip.
-   Opening and closing odometer readings must be non-negative.
-   Closing odometer must be greater than or equal to opening odometer.
-   A completed trip must have actual start, actual end and closing
    odometer.
-   Maintenance completion requires resolution notes.
-   A vehicle under active maintenance cannot be assigned to a new trip.
-   Only authorised roles can approve, dispatch, complete or cancel
    trips.

**Concurrency:** A simple "check then save" overlap validation can race
when two dispatchers act simultaneously. For a production
implementation, add a transaction-safe allocation strategy (for example,
a dedicated reservation/allocation record and appropriate locking/unique
constraints) and test concurrent dispatch. The POC should document this
limitation rather than claiming the check is race-proof.

### 6.3 Vehicle status management

For the POC, keep vehicle status explicit and update it only through
controlled server-side lifecycle methods:

-   Dispatch trip → vehicle becomes `On Trip`.
-   Complete or validly cancel trip → vehicle becomes `Available`,
    unless an open maintenance request requires `Maintenance`.
-   Open maintenance request → vehicle becomes `Maintenance`, subject to
    the chosen policy for a vehicle already on a trip.
-   Complete maintenance → vehicle becomes `Available` only if there is
    no other blocking condition.

Avoid arbitrary status edits by general users. Consider deriving
availability from active trips and maintenance records in a later
iteration; for the POC, a controlled status field is easier to
demonstrate but must be reconciled consistently.

------------------------------------------------------------------------

## 7. Roles and permissions

Create roles through **Role** and assign DocType permissions through
**Role Permission Manager**. Suggested minimum roles:

  -----------------------------------------------------------------------
  Role                    Responsibilities        Access summary
  ----------------------- ----------------------- -----------------------
  Fleet Administrator     Configure masters and   Full access to fleet
                          users                   masters and setup

  Dispatcher              Plan and create trips   Create/read trips;
                                                  cannot approve

  Fleet Manager           Approve and oversee     Read all trips;
                          operations              approve/reject; manage
                                                  maintenance

  Driver (optional POC    View assigned trips     Read own assigned trips
  role)                                           only; no master-data
                                                  access

  Fleet Auditor           Review records and      Read-only access to
  (optional)              reports                 approved operational
                                                  data
  -----------------------------------------------------------------------

### Permission design checklist

-   Grant only the minimum required permissions for each DocType.
-   Use document-level permission checks for "own/assigned" records; a
    role alone does not restrict rows.
-   Use User Permissions where a user should be limited to a specific
    linked master, such as a company or branch.
-   Use `permission_query_conditions` for list-query filtering where
    appropriate, and `has_permission` for document-level checks. Keep
    these rules server-side and covered by tests.
-   Protect sensitive Driver fields with appropriate permission levels
    and field-level permission configuration; verify API responses as
    well as Desk rendering.
-   Do not use hidden fields, client scripts or filtered Link queries as
    security controls.
-   Review access using test accounts for each role, including direct
    REST API calls.

------------------------------------------------------------------------

## 8. Suggested app structure

Create a standard Frappe custom app. A possible structure:

``` text
fleet_management/
├── fleet_management/
│   ├── hooks.py
│   ├── modules.txt
│   ├── config/
│   │   ├── desktop.py
│   │   └── ...
│   ├── fleet_management/
│   │   ├── doctype/
│   │   │   ├── vehicle/
│   │   │   │   ├── vehicle.json
│   │   │   │   └── vehicle.py
│   │   │   ├── driver/
│   │   │   ├── fleet_location/
│   │   │   ├── trip/
│   │   │   │   ├── trip.json
│   │   │   │   └── trip.py
│   │   │   ├── trip_expense/
│   │   │   └── maintenance_request/
│   │   ├── report/
│   │   └── workspace/
│   ├── api/
│   │   └── trip.py
│   └── patches/
├── README.md
├── pyproject.toml
└── license.txt
```

The exact generated paths can vary by Frappe version and module naming.
Keep each DocType's controller close to its DocType. Avoid putting all
business logic in `hooks.py` or a single generic utility module.

------------------------------------------------------------------------

## 9. Build and setup instructions

### 9.1 Prerequisites

Use the official Frappe installation guide for the selected release and
operating system. Typical development prerequisites include:

-   A supported Linux environment (commonly Ubuntu) or a supported
    container-based development environment.
-   Python version supported by the selected Frappe branch.
-   Node.js and package manager versions supported by that branch.
-   Redis, MariaDB and required build/system packages.
-   Bench CLI.

**Version policy:** Select a supported Frappe major version before
starting. Pin the Frappe branch and app dependencies together. Do not
mix instructions or dependencies from different major versions. Confirm
the current compatibility matrix in the official Frappe documentation.

### 9.2 Create a bench and site

The following is an illustrative Bench workflow. Run commands in a
development environment and adjust branch, database credentials and site
name to your organisation's standards.

``` bash
# Install Bench using the method recommended for your environment.
# Then initialise a bench with the chosen supported Frappe branch.
bench init --frappe-branch version-15 fleet-bench
cd fleet-bench

# Create a development site.
bench new-site fleet.local

# Create the custom app.
bench new-app fleet_management

# Install the app on the site.
bench --site fleet.local install-app fleet_management

# Start the development services.
bench start
```

If your organisation has standardised on another supported major
version, replace `version-15` with that release branch and validate all
dependencies against it. Do not use the example branch blindly for a new
production deployment.

### 9.3 Create the module and DocTypes

1.  Open the site in a browser and sign in with an Administrator
    account.
2.  Create a module named **Fleet Management** (or use the module
    created with the app).
3.  Create the DocTypes from Section 5.
4.  Use **Naming Series** for Vehicle, Trip and Maintenance Request
    identifiers.
5.  Configure Link fields and the Trip Expense child table.
6.  Configure required fields, read-only derived fields, options and
    field-level permission levels.
7.  Enable change tracking/versioning where appropriate.
8.  Export fixtures only for configuration records that should be
    version-controlled (for example, selected
    roles/workflows/workspaces). Avoid exporting environment-specific
    users or secrets.

You can create DocTypes through Desk during the POC, then commit the
generated JSON and controller files into the custom app. For a
team-maintained implementation, review generated metadata in source
control and deploy it through migrations.

### 9.4 Add controllers and validations

Implement validation in `validate`, and lifecycle effects in explicit
document methods or appropriate hooks such as `on_submit`, `on_cancel`
and `on_update_after_submit`, depending on the chosen DocType lifecycle.

Illustrative controller pattern (adapt field names and lifecycle to the
actual DocType):

``` python
import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime


class Trip(Document):
    def validate(self):
        self.validate_dates()
        self.validate_vehicle_and_driver()
        self.validate_odometer()

    def validate_dates(self):
        if self.planned_start and self.planned_end:
            if get_datetime(self.planned_end) <= get_datetime(self.planned_start):
                frappe.throw("Planned end must be later than planned start.")

    def validate_vehicle_and_driver(self):
        if self.vehicle:
            vehicle = frappe.get_doc("Vehicle", self.vehicle)
            if vehicle.status in ("Inactive", "Maintenance"):
                frappe.throw("The selected vehicle is not available for dispatch.")

        if self.driver:
            driver = frappe.get_doc("Driver", self.driver)
            if driver.status != "Active":
                frappe.throw("The selected driver is not active.")
            if driver.license_expiry_date and self.planned_start:
                if driver.license_expiry_date < get_datetime(self.planned_start).date():
                    frappe.throw("The driver's licence is not valid for the planned start date.")

    def validate_odometer(self):
        if self.opening_odometer is not None and self.opening_odometer < 0:
            frappe.throw("Opening odometer cannot be negative.")
        if self.closing_odometer is not None and self.closing_odometer < 0:
            frappe.throw("Closing odometer cannot be negative.")
        if (
            self.opening_odometer is not None
            and self.closing_odometer is not None
            and self.closing_odometer < self.opening_odometer
        ):
            frappe.throw("Closing odometer cannot be less than opening odometer.")
```

This is a starting pattern, not a complete controller. Add overlap
checks, workflow transition guards, maintenance conflict checks and
permission enforcement before demonstrating the full flow. Ensure that
any status changes are performed server-side and are transactionally
consistent with the trip transition.

### 9.5 Configure Workflow

In Desk:

1.  Create a Workflow named **Trip Approval Workflow**.
2.  Select the Trip DocType.
3.  Define the states and transitions from Section 6.
4.  Assign allowed roles to each transition.
5.  Configure the initial state and document state mapping carefully.
6.  Test every transition with separate Dispatcher and Fleet Manager
    accounts.
7.  Verify that a user cannot bypass the workflow through direct API
    calls or crafted requests.

Use a separate workflow for Maintenance Request if approval or
controlled closure is required.

### 9.6 Create workspace and reports

Create a **Fleet Operations** Workspace with shortcuts to:

-   Vehicles
-   Drivers
-   Fleet Locations
-   Trips
-   Maintenance Requests

Add dashboard charts or reports for:

-   Trips by status
-   Available vs On Trip vs Maintenance vehicles
-   Distance travelled by date range
-   Vehicle utilisation
-   Maintenance requests by status
-   Trip expense totals by type and period

Keep reports permission-aware. Avoid reports that expose driver personal
data to broad audiences.

------------------------------------------------------------------------

## 10. API and integration conventions

Frappe automatically exposes standard resource APIs for DocTypes. For
example, an authenticated client can use the resource endpoint pattern:

``` text
GET    /api/resource/Vehicle
GET    /api/resource/Vehicle/{name}
POST   /api/resource/Trip
PUT    /api/resource/Trip/{name}
```

A purpose-built method can be exposed with `@frappe.whitelist()` for
actions such as dispatch or completion. Example pattern:

``` python
import frappe


@frappe.whitelist()
def get_my_active_trips():
    # Apply explicit permission and assignment filtering.
    # Do not trust a client-supplied user identity.
    user = frappe.session.user
    return frappe.get_list(
        "Trip",
        filters={"driver_user": user, "status": "In Progress"},
        fields=["name", "vehicle", "origin", "destination", "planned_start"],
    )
```

The field `driver_user` is illustrative; add a deliberate relationship
from Driver to User if this use case is required.

### API standards

-   Use Frappe authentication mechanisms; use token authentication for
    trusted integrations and protect credentials as secrets.
-   Keep methods small, resource-oriented and permission-aware.
-   Validate all inputs server-side; never trust client-side field
    filters.
-   Prefer `frappe.get_list` when permission filtering is required.
    Understand the permission semantics before using `frappe.get_all`.
-   Do not expose unrestricted whitelisted methods or use
    `ignore_permissions=True` as a shortcut.
-   Return stable, documented response shapes and meaningful error
    messages.
-   Add API tests for unauthorised, invalid, boundary and successful
    requests.
-   Apply rate limiting and network restrictions at the appropriate
    infrastructure layer for externally exposed endpoints.
-   Version custom API contracts if mobile/external clients depend on
    them.

------------------------------------------------------------------------

## 11. Testing strategy and acceptance criteria

### Minimum test layers

  -----------------------------------------------------------------------
  Layer                               What to test
  ----------------------------------- -----------------------------------
  DocType unit tests                  Required fields, date validation,
                                      odometer calculations

  Business-rule tests                 Driver licence, vehicle
                                      eligibility, overlapping trips

  Workflow tests                      Allowed and denied transitions by
                                      role

  Permission tests                    Desk and REST access for each role

  Integration tests                   Dispatch → complete → vehicle
                                      status reconciliation

  Regression tests                    Maintenance conflict and
                                      cancellation paths

  Concurrency tests                   Two dispatch requests competing for
                                      the same vehicle/driver
  -----------------------------------------------------------------------

Use Frappe's test framework and run tests against a disposable test
site. Keep test data deterministic and avoid relying on production
records.

### POC acceptance checklist

-   [ ] Fleet Administrator can create and maintain vehicles, drivers
    and locations.
-   [ ] Dispatcher can create a trip and submit it for approval.
-   [ ] Fleet Manager can approve/reject; Dispatcher cannot approve
    their own request unless explicitly allowed by policy.
-   [ ] Inactive vehicles and drivers with expired licences cannot be
    dispatched.
-   [ ] Overlapping trips for the same vehicle or driver are rejected.
-   [ ] Dispatch captures actual start and opening odometer.
-   [ ] Completion captures actual end and closing odometer and
    calculates distance.
-   [ ] Trip expenses can be added and reported.
-   [ ] Open maintenance blocks new dispatches for the affected vehicle.
-   [ ] Vehicle status is reconciled after
    completion/cancellation/maintenance closure.
-   [ ] Users cannot access restricted records or actions through direct
    REST calls.
-   [ ] Workspace and reports provide a clear operational summary.
-   [ ] Automated tests cover critical validations and permission
    boundaries.

------------------------------------------------------------------------

## 12. Engineering standards for an organisation

### Source control and code review

-   Keep the custom app in a dedicated Git repository.
-   Use protected `main`/release branches and pull requests.
-   Require review for DocType schema changes, permission changes,
    hooks, patches and API changes.
-   Commit generated DocType JSON, Python controllers, fixtures and
    tests.
-   Do not commit site-specific configuration, database dumps, private
    files, credentials or secrets.
-   Keep commits focused and include migration/rollback considerations
    in PR descriptions.

### Code quality

-   Follow the Python style and linting conventions adopted by the
    organisation.
-   Keep business logic in controllers or domain services, not client
    scripts.
-   Avoid duplicate validation across Desk and API layers; centralise
    authoritative rules server-side.
-   Use framework APIs and ORM. Any raw SQL must be parameterised,
    reviewed and justified.
-   Avoid unnecessary `frappe.db.commit()` calls; understand the
    request/job transaction lifecycle.
-   Avoid broad exception swallowing. Log actionable context without
    leaking personal or secret data.
-   Use patches for controlled data/schema transformations; make patches
    safe to run once and review their rollback strategy.

### Security and privacy

-   Use least-privilege roles and review permissions for every DocType
    and report.
-   Treat driver licence, phone and identity data as sensitive personal
    information.
-   Use HTTPS, secure session/token handling and secret management.
-   Restrict File attachments and verify download permissions.
-   Do not log authentication tokens, personal identifiers or sensitive
    request payloads.
-   Establish retention, deletion and access-review policies before real
    personal data is loaded.
-   Keep framework and app dependencies patched; scan dependencies and
    review security advisories.

### Operations and deployment

-   Maintain separate development, staging/UAT and production sites.
-   Deploy through a repeatable CI/CD process; do not make untracked
    production Desk changes.
-   Back up database and files and periodically test restoration.
-   Run migrations during controlled releases and validate them in
    staging first.
-   Monitor application errors, background jobs, queue health, database
    capacity and scheduled jobs.
-   Document site-specific settings and keep secrets outside source
    control.
-   Define an operational owner for backup, restore, upgrades and
    incident response.

------------------------------------------------------------------------

## 13. POC delivery plan

  ------------------------------------------------------------------------
  Phase                   Work                    Exit criteria
  ----------------------- ----------------------- ------------------------
  1\. Foundation          Bench, site, app, Git   App installs cleanly on
                          repository, roles       a fresh site

  2\. Masters             Vehicle, Driver, Fleet  Master data can be
                          Location                created with validations

  3\. Trip workflow       Trip, child expenses,   Approval-to-completion
                          workflow and rules      demo succeeds

  4\. Maintenance         Maintenance Request and Maintenance prevents
                          vehicle blocking        invalid dispatch

  5\. Visibility          Workspace, reports and  Fleet Manager can review
                          dashboard               operations

  6\. Quality gate        Tests, permission       Acceptance checklist
                          review, deployment      passes on staging
                          notes                   
  ------------------------------------------------------------------------

A small team can timebox this into a short POC, but estimates should be
made after confirming the Frappe version, workflow complexity,
deployment environment and whether the POC requires scripted DocType
creation or Desk-first configuration.

------------------------------------------------------------------------

## 14. Known POC limitations and production gaps

The following must be addressed before production use:

1.  **Concurrent allocation:** Ensure vehicle/driver reservation is
    race-safe under simultaneous dispatch.
2.  **Status reconciliation:** Define a single authoritative rule for
    availability across trips and maintenance.
3.  **Multi-company/branch:** Define company, branch, cost centre and
    data-isolation requirements if applicable.
4.  **GPS and mobile:** Design device identity, location consent,
    offline sync, event ordering and conflict resolution separately.
5.  **Audit and compliance:** Confirm retention, audit evidence,
    document immutability and regulatory requirements.
6.  **Scale:** Load-test list views, reports, indexes, background queues
    and expected transaction volume.
7.  **Operational resilience:** Validate backups, restore, monitoring,
    upgrades and disaster recovery.
8.  **Financial controls:** Integrate expenses with an approved
    accounting process if financial posting is required.
9.  **Data protection:** Complete privacy/security review before using
    real driver and vehicle documents.

Do not describe the POC as production-ready until these gaps have
owners, designs and acceptance evidence.

------------------------------------------------------------------------

## 15. Demo script (10--15 minutes)

1.  Sign in as Fleet Administrator and show Vehicle, Driver and Location
    masters.
2.  Show an expired-licence driver and explain why the driver cannot be
    dispatched.
3.  Sign in as Dispatcher and create a trip for an available vehicle and
    active driver.
4.  Attempt an overlapping trip and demonstrate server-side rejection.
5.  Submit the valid trip for approval.
6.  Sign in as Fleet Manager and approve it.
7.  Dispatch the trip and enter opening odometer.
8.  Add a fuel/toll expense and complete the trip with closing odometer.
9.  Show the calculated distance and vehicle status update.
10. Create a maintenance request and demonstrate that the vehicle is
    blocked from new trips.
11. Finish on the Fleet Operations Workspace and review the reports.

### POC success measure

The POC is successful when a stakeholder can complete the full lifecycle
using Frappe Desk, see the state and audit history at each step, and
verify that invalid operations are rejected by server-side rules and
permissions.

------------------------------------------------------------------------

## 16. Official references

Use documentation matching the exact Frappe major version selected for
the POC:

-   Frappe Framework documentation: https://docs.frappe.io/framework
-   Bench documentation: https://docs.frappe.io/framework/user/en/bench
-   DocType documentation:
    https://docs.frappe.io/framework/user/en/basics/doctypes
-   REST API documentation:
    https://docs.frappe.io/framework/user/en/api/rest
-   Server Script documentation:
    https://docs.frappe.io/framework/user/en/desk/scripting/server-script
-   Hooks documentation:
    https://docs.frappe.io/framework/user/en/python-api/hooks
-   Role and permissions documentation:
    https://docs.frappe.io/framework/user/en/basics/users-and-permissions

> Documentation URLs and installation prerequisites can change between
> Frappe releases. Confirm the selected release's documentation and
> supported dependency matrix before implementation.
# Fleet Management System --- Frappe POC

> **Purpose:** A small, demonstrable Fleet Management System built
> entirely on the Frappe Framework and Desk.\
> **Audience:** Engineering leads, Frappe developers, solution
> architects and POC stakeholders.\
> **Status:** Proof of Concept (POC) --- not production-ready without
> the hardening work listed below.

------------------------------------------------------------------------

## 1. POC objectives

Build a working fleet operations workflow using native Frappe
capabilities rather than introducing a separate application backend or
frontend.

The POC should demonstrate that Frappe can provide:

-   Master-data management for vehicles, drivers and locations.
-   Vehicle allocation to a driver for a defined period.
-   Trip creation, dispatch, completion and cancellation.
-   Odometer and fuel/expense capture.
-   Vehicle maintenance logging and availability control.
-   Role-based access, workflow approvals, activity history and reports.
-   REST API access for a future mobile application or external
    integration.

### Explicitly out of scope

Do not expand the POC into a full transport-management or telematics
platform. The first iteration excludes live GPS tracking, route
optimisation, payroll, fuel-card integrations, FASTag integrations,
vendor procurement, accounting integration, driver mobile app,
preventive-maintenance prediction and multi-company inter-company
settlement.

These can be evaluated after the core workflow is validated.

------------------------------------------------------------------------

## 2. Recommended implementation approach

Use a **custom Frappe app** (for example, `fleet_management`) installed
on a supported Frappe site. Model the business domain with DocTypes and
use the framework's built-in capabilities wherever practical.

  -----------------------------------------------------------------------
  Concern                             POC implementation
  ----------------------------------- -----------------------------------
  User interface                      Frappe Desk forms, List Views,
                                      reports and workspace

  Domain model                        Custom DocTypes, Link fields, child
                                      tables and naming series

  Business rules                      DocType controller validations and
                                      lifecycle hooks

  State transitions                   Frappe Workflow for Trip and
                                      Maintenance Request

  Authorization                       Roles, DocType permissions, User
                                      Permissions and permission query
                                      conditions where required

  Persistence                         MariaDB via Frappe ORM; no direct
                                      SQL for normal CRUD

  Background work                     `frappe.enqueue` / scheduled jobs
                                      only for genuinely asynchronous
                                      tasks

  Integration                         Frappe REST API and whitelisted
                                      methods with explicit permission
                                      checks

  Audit                               Document Versioning,
                                      comments/timeline and standard
                                      creation/modification metadata

  Reporting                           Query Reports / Script Reports and
                                      Dashboard Charts

  Deployment                          Bench-managed app, site
                                      configuration, migrations and
                                      controlled releases
  -----------------------------------------------------------------------

**Design principle:** Keep the POC deliberately Frappe-native. Do not
add a separate microservice, custom SPA or external workflow engine
unless a demonstrated requirement cannot be met cleanly in Frappe.

------------------------------------------------------------------------

## 3. High-level architecture

``` mermaid
flowchart TB
    U[Operations User / Fleet Manager]
    A[Administrator]
    M[Future Mobile App / External Client]

    subgraph FRAPPE["Frappe Site"]
      subgraph UX["Presentation Layer"]
        D[Desk Forms and List Views]
        W[Workspace and Dashboards]
        R[Reports]
      end

      subgraph APP["Application Layer — fleet_management"]
        API[REST API / Whitelisted Methods]
        DOC[DocTypes and Document Controllers]
        WF[Workflows and State Transitions]
        VAL[Validations and Business Rules]
        JOB[Background Jobs / Scheduler]
        PERM[Roles and Permission Checks]
      end

      subgraph CORE["Frappe Framework Services"]
        ORM[Frappe ORM]
        AUTH[Authentication and Authorization]
        AUDIT[Timeline, Versioning and Activity]
        QUEUE[Background Job Queue]
      end
    end

    DB[(MariaDB)]
    REDIS[(Redis Cache / Queue)]
    FILES[(File Storage)]

    U --> D
    U --> W
    U --> R
    A --> D
    M --> API

    D --> DOC
    W --> DOC
    R --> ORM
    API --> AUTH
    API --> PERM
    API --> DOC
    DOC --> WF
    DOC --> VAL
    DOC --> PERM
    DOC --> ORM
    DOC --> AUDIT
    JOB --> QUEUE
    QUEUE --> REDIS
    JOB --> DOC
    ORM --> DB
    AUDIT --> DB
    DOC --> FILES
```

### Architecture notes

1.  **Presentation:** Use Desk as the primary POC interface. Configure
    Workspace shortcuts, List Views, dashboards and reports for
    operational users.
2.  **Application:** Put validations in DocType controllers so they
    apply to Desk, REST API and background execution paths. Use
    whitelisted methods only for operations that need a purpose-built
    API.
3.  **Workflow:** Use Frappe Workflow for user-driven state transitions
    and role-based approval. Do not rely on a client script to enforce a
    business rule.
4.  **Persistence:** Use the Frappe ORM (`frappe.get_doc`,
    `frappe.new_doc`, `frappe.db.get_value`, etc.). Avoid direct
    database writes and raw SQL unless a reviewed reporting/query use
    case justifies it.
5.  **Security:** UI visibility is not authorization. Enforce access
    using DocType permissions, document-level permission logic and
    server-side checks.
6.  **Async processing:** Use background jobs for non-interactive work;
    do not enqueue simple validations or operations that must finish
    before a document can be saved.

------------------------------------------------------------------------

## 4. Functional scope and demo flow

The POC should support the following end-to-end scenario:

1.  Fleet Admin creates a vehicle and assigns it an active status.
2.  Fleet Admin creates a driver record and records licence validity.
3.  Dispatcher creates a trip, selecting a vehicle, driver, origin,
    destination and planned dates.
4.  On submission, server-side validation checks that the vehicle and
    driver are eligible and do not have overlapping active trips.
5.  Dispatcher submits the trip for approval. An authorised Fleet
    Manager approves or rejects it.
6.  On dispatch, the trip records the opening odometer. On completion,
    the closing odometer and actual end time are captured.
7.  The system calculates distance travelled and records trip expenses.
8.  If a vehicle requires repair, a Maintenance Request is created and
    the vehicle is marked unavailable for new trips until released.
9.  Fleet Manager reviews operational reports: active trips, vehicle
    utilisation, maintenance due and trip costs.

### Suggested demo data

-   3 vehicles: one available, one on an active trip, one under
    maintenance.
-   4 drivers: three active and one with an expired licence.
-   3 locations: Depot, Customer Site A and Customer Site B.
-   5 trips: Draft, Pending Approval, Approved, In Progress and
    Completed.
-   2 maintenance records: one Open and one Completed.

Use fictional data only. Do not load real driver licence numbers,
personal phone numbers or vehicle documents into a demo site.

------------------------------------------------------------------------

## 5. Domain model and DocTypes

Use the following DocTypes as the initial model. Keep the first POC
intentionally small; add fields only when a workflow or report needs
them.

### 5.1 Master DocTypes

#### Vehicle

  -------------------------------------------------------------------------
  Field                     Type                    Notes
  ------------------------- ----------------------- -----------------------
  `vehicle_name`            Data                    Human-readable label

  `registration_number`     Data, Unique            Normalised
                                                    registration; unique
                                                    constraint/validation

  `vehicle_type`            Link / Select           E.g. Car, Van, Truck

  `make`                    Data                    Manufacturer

  `model`                   Data                    Model

  `manufacturing_year`      Int                     Optional

  `capacity`                Float                   Define unit
                                                    consistently

  `fuel_type`               Select                  Petrol, Diesel, CNG,
                                                    EV, Other

  `current_odometer`        Float                   Latest verified
                                                    odometer reading

  `status`                  Select                  Available, On Trip,
                                                    Maintenance, Inactive

  `last_service_date`       Date                    Optional

  `next_service_due_date`   Date                    Optional
  -------------------------------------------------------------------------

**Naming:** `VEH-.YYYY.-.#####` or another agreed naming series.\
**Validation:** Registration number must be unique after normalisation.
Odometer cannot be negative. A vehicle in Maintenance or Inactive status
cannot be dispatched.

#### Driver

  Field                   Type         Notes
  ----------------------- ------------ ----------------------------------------
  `driver_name`           Data         Required
  `employee_id`           Data         Unique if sourced from HR
  `phone`                 Phone        Restrict access to appropriate roles
  `license_number`        Data         Treat as sensitive personal data
  `license_expiry_date`   Date         Required for dispatch eligibility
  `status`                Select       Active, Inactive, Suspended
  `notes`                 Small Text   Avoid sensitive or unnecessary details

**Validation:** Driver must be Active and licence must be valid on the
planned trip date. Do not expose licence data to general users or
include it in broad reports.

#### Fleet Location

  Field             Type           Notes
  ----------------- -------------- -----------------------------------------
  `location_name`   Data           Required
  `location_code`   Data, Unique   Stable reference
  `address`         Small Text     Optional
  `is_active`       Check          Prevent selection of inactive locations

### 5.2 Transaction DocTypes

#### Trip

  ---------------------------------------------------------------------------
  Field                   Type                    Notes
  ----------------------- ----------------------- ---------------------------
  `trip_id`               Naming Series           e.g. `TRIP-.YYYY.-.#####`

  `vehicle`               Link → Vehicle          Required

  `driver`                Link → Driver           Required

  `origin`                Link → Fleet Location   Required

  `destination`           Link → Fleet Location   Required

  `planned_start`         Datetime                Required

  `planned_end`           Datetime                Required

  `actual_start`          Datetime                Set on dispatch

  `actual_end`            Datetime                Set on completion

  `opening_odometer`      Float                   Captured at dispatch

  `closing_odometer`      Float                   Captured at completion

  `distance_travelled`    Float                   Derived server-side

  `purpose`               Small Text              Business reason

  `status`                Workflow State          Draft, Pending Approval,
                                                  Approved, In Progress,
                                                  Completed, Rejected,
                                                  Cancelled

  `trip_expenses`         Table → Trip Expense    Child table

  `remarks`               Text                    Optional
  ---------------------------------------------------------------------------

#### Trip Expense (Child Table)

  Field            Type       Notes
  ---------------- ---------- ----------------------------
  `expense_type`   Select     Fuel, Toll, Parking, Other
  `amount`         Currency   Must be non-negative
  `expense_date`   Date       Required
  `reference`      Data       Receipt/reference number
  `attachment`     Attach     Optional receipt

Do not store payment-card details. For the POC, expense capture is
informational and is not an accounting posting.

#### Maintenance Request

  -----------------------------------------------------------------------
  Field                   Type                    Notes
  ----------------------- ----------------------- -----------------------
  `vehicle`               Link → Vehicle          Required

  `reported_on`           Datetime                Default current time

  `issue_type`            Select                  Scheduled Service,
                                                  Breakdown, Inspection,
                                                  Other

  `description`           Text Editor / Small     Required
                          Text                    

  `priority`              Select                  Low, Medium, High,
                                                  Critical

  `odometer_reading`      Float                   Must not be less than
                                                  last verified reading

  `status`                Workflow State          Open, In Progress,
                                                  Completed, Cancelled

  `service_date`          Date                    Optional

  `cost`                  Currency                Optional POC value

  `resolution_notes`      Text                    Required on completion
  -----------------------------------------------------------------------

### 5.3 Relationships

``` mermaid
erDiagram
    VEHICLE ||--o{ TRIP : assigned_to
    DRIVER ||--o{ TRIP : drives
    FLEET_LOCATION ||--o{ TRIP : origin
    FLEET_LOCATION ||--o{ TRIP : destination
    TRIP ||--o{ TRIP_EXPENSE : contains
    VEHICLE ||--o{ MAINTENANCE_REQUEST : has
```

The diagram shows logical relationships. In Frappe, implement these with
Link fields and child tables; do not create a separate SQL schema
manually.

------------------------------------------------------------------------

## 6. Workflow and business rules

### 6.1 Trip lifecycle

``` mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> PendingApproval: Submit
    PendingApproval --> Approved: Approve
    PendingApproval --> Rejected: Reject
    Rejected --> Draft: Amend and resubmit
    Approved --> InProgress: Dispatch
    InProgress --> Completed: Complete trip
    Draft --> Cancelled: Cancel
    PendingApproval --> Cancelled: Cancel
    Approved --> Cancelled: Cancel before dispatch
    Completed --> [*]
    Cancelled --> [*]
```

Configure the exact state transitions and permitted roles in Frappe
Workflow. The POC may use `docstatus` for draft/submitted/cancelled
document lifecycle, but do not confuse `docstatus` with a business
workflow state. Decide whether Trip is submittable and keep the workflow
design consistent.

### 6.2 Required server-side validations

Implement and test these rules in the relevant DocType controller:

-   Vehicle and driver must be active.
-   Driver licence must be valid through the planned trip date.
-   Vehicle must not be Inactive or in Maintenance at dispatch.
-   No overlapping non-cancelled trips for the same vehicle.
-   No overlapping non-cancelled trips for the same driver.
-   Planned end must be later than planned start.
-   Origin and destination must differ unless the use case explicitly
    permits a local/round trip.
-   Opening and closing odometer readings must be non-negative.
-   Closing odometer must be greater than or equal to opening odometer.
-   A completed trip must have actual start, actual end and closing
    odometer.
-   Maintenance completion requires resolution notes.
-   A vehicle under active maintenance cannot be assigned to a new trip.
-   Only authorised roles can approve, dispatch, complete or cancel
    trips.

**Concurrency:** A simple "check then save" overlap validation can race
when two dispatchers act simultaneously. For a production
implementation, add a transaction-safe allocation strategy (for example,
a dedicated reservation/allocation record and appropriate locking/unique
constraints) and test concurrent dispatch. The POC should document this
limitation rather than claiming the check is race-proof.

### 6.3 Vehicle status management

For the POC, keep vehicle status explicit and update it only through
controlled server-side lifecycle methods:

-   Dispatch trip → vehicle becomes `On Trip`.
-   Complete or validly cancel trip → vehicle becomes `Available`,
    unless an open maintenance request requires `Maintenance`.
-   Open maintenance request → vehicle becomes `Maintenance`, subject to
    the chosen policy for a vehicle already on a trip.
-   Complete maintenance → vehicle becomes `Available` only if there is
    no other blocking condition.

Avoid arbitrary status edits by general users. Consider deriving
availability from active trips and maintenance records in a later
iteration; for the POC, a controlled status field is easier to
demonstrate but must be reconciled consistently.

------------------------------------------------------------------------

## 7. Roles and permissions

Create roles through **Role** and assign DocType permissions through
**Role Permission Manager**. Suggested minimum roles:

  -----------------------------------------------------------------------
  Role                    Responsibilities        Access summary
  ----------------------- ----------------------- -----------------------
  Fleet Administrator     Configure masters and   Full access to fleet
                          users                   masters and setup

  Dispatcher              Plan and create trips   Create/read trips;
                                                  cannot approve

  Fleet Manager           Approve and oversee     Read all trips;
                          operations              approve/reject; manage
                                                  maintenance

  Driver (optional POC    View assigned trips     Read own assigned trips
  role)                                           only; no master-data
                                                  access

  Fleet Auditor           Review records and      Read-only access to
  (optional)              reports                 approved operational
                                                  data
  -----------------------------------------------------------------------

### Permission design checklist

-   Grant only the minimum required permissions for each DocType.
-   Use document-level permission checks for "own/assigned" records; a
    role alone does not restrict rows.
-   Use User Permissions where a user should be limited to a specific
    linked master, such as a company or branch.
-   Use `permission_query_conditions` for list-query filtering where
    appropriate, and `has_permission` for document-level checks. Keep
    these rules server-side and covered by tests.
-   Protect sensitive Driver fields with appropriate permission levels
    and field-level permission configuration; verify API responses as
    well as Desk rendering.
-   Do not use hidden fields, client scripts or filtered Link queries as
    security controls.
-   Review access using test accounts for each role, including direct
    REST API calls.

------------------------------------------------------------------------

## 8. Suggested app structure

Create a standard Frappe custom app. A possible structure:

``` text
fleet_management/
├── fleet_management/
│   ├── hooks.py
│   ├── modules.txt
│   ├── config/
│   │   ├── desktop.py
│   │   └── ...
│   ├── fleet_management/
│   │   ├── doctype/
│   │   │   ├── vehicle/
│   │   │   │   ├── vehicle.json
│   │   │   │   └── vehicle.py
│   │   │   ├── driver/
│   │   │   ├── fleet_location/
│   │   │   ├── trip/
│   │   │   │   ├── trip.json
│   │   │   │   └── trip.py
│   │   │   ├── trip_expense/
│   │   │   └── maintenance_request/
│   │   ├── report/
│   │   └── workspace/
│   ├── api/
│   │   └── trip.py
│   └── patches/
├── README.md
├── pyproject.toml
└── license.txt
```

The exact generated paths can vary by Frappe version and module naming.
Keep each DocType's controller close to its DocType. Avoid putting all
business logic in `hooks.py` or a single generic utility module.

------------------------------------------------------------------------

## 9. Build and setup instructions

### 9.1 Prerequisites

Use the official Frappe installation guide for the selected release and
operating system. Typical development prerequisites include:

-   A supported Linux environment (commonly Ubuntu) or a supported
    container-based development environment.
-   Python version supported by the selected Frappe branch.
-   Node.js and package manager versions supported by that branch.
-   Redis, MariaDB and required build/system packages.
-   Bench CLI.

**Version policy:** Select a supported Frappe major version before
starting. Pin the Frappe branch and app dependencies together. Do not
mix instructions or dependencies from different major versions. Confirm
the current compatibility matrix in the official Frappe documentation.

### 9.2 Create a bench and site

The following is an illustrative Bench workflow. Run commands in a
development environment and adjust branch, database credentials and site
name to your organisation's standards.

``` bash
# Install Bench using the method recommended for your environment.
# Then initialise a bench with the chosen supported Frappe branch.
bench init --frappe-branch version-15 fleet-bench
cd fleet-bench

# Create a development site.
bench new-site fleet.local

# Create the custom app.
bench new-app fleet_management

# Install the app on the site.
bench --site fleet.local install-app fleet_management

# Start the development services.
bench start
```

If your organisation has standardised on another supported major
version, replace `version-15` with that release branch and validate all
dependencies against it. Do not use the example branch blindly for a new
production deployment.

### 9.3 Create the module and DocTypes

1.  Open the site in a browser and sign in with an Administrator
    account.
2.  Create a module named **Fleet Management** (or use the module
    created with the app).
3.  Create the DocTypes from Section 5.
4.  Use **Naming Series** for Vehicle, Trip and Maintenance Request
    identifiers.
5.  Configure Link fields and the Trip Expense child table.
6.  Configure required fields, read-only derived fields, options and
    field-level permission levels.
7.  Enable change tracking/versioning where appropriate.
8.  Export fixtures only for configuration records that should be
    version-controlled (for example, selected
    roles/workflows/workspaces). Avoid exporting environment-specific
    users or secrets.

You can create DocTypes through Desk during the POC, then commit the
generated JSON and controller files into the custom app. For a
team-maintained implementation, review generated metadata in source
control and deploy it through migrations.

### 9.4 Add controllers and validations

Implement validation in `validate`, and lifecycle effects in explicit
document methods or appropriate hooks such as `on_submit`, `on_cancel`
and `on_update_after_submit`, depending on the chosen DocType lifecycle.

Illustrative controller pattern (adapt field names and lifecycle to the
actual DocType):

``` python
import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime


class Trip(Document):
    def validate(self):
        self.validate_dates()
        self.validate_vehicle_and_driver()
        self.validate_odometer()

    def validate_dates(self):
        if self.planned_start and self.planned_end:
            if get_datetime(self.planned_end) <= get_datetime(self.planned_start):
                frappe.throw("Planned end must be later than planned start.")

    def validate_vehicle_and_driver(self):
        if self.vehicle:
            vehicle = frappe.get_doc("Vehicle", self.vehicle)
            if vehicle.status in ("Inactive", "Maintenance"):
                frappe.throw("The selected vehicle is not available for dispatch.")

        if self.driver:
            driver = frappe.get_doc("Driver", self.driver)
            if driver.status != "Active":
                frappe.throw("The selected driver is not active.")
            if driver.license_expiry_date and self.planned_start:
                if driver.license_expiry_date < get_datetime(self.planned_start).date():
                    frappe.throw("The driver's licence is not valid for the planned start date.")

    def validate_odometer(self):
        if self.opening_odometer is not None and self.opening_odometer < 0:
            frappe.throw("Opening odometer cannot be negative.")
        if self.closing_odometer is not None and self.closing_odometer < 0:
            frappe.throw("Closing odometer cannot be negative.")
        if (
            self.opening_odometer is not None
            and self.closing_odometer is not None
            and self.closing_odometer < self.opening_odometer
        ):
            frappe.throw("Closing odometer cannot be less than opening odometer.")
```

This is a starting pattern, not a complete controller. Add overlap
checks, workflow transition guards, maintenance conflict checks and
permission enforcement before demonstrating the full flow. Ensure that
any status changes are performed server-side and are transactionally
consistent with the trip transition.

### 9.5 Configure Workflow

In Desk:

1.  Create a Workflow named **Trip Approval Workflow**.
2.  Select the Trip DocType.
3.  Define the states and transitions from Section 6.
4.  Assign allowed roles to each transition.
5.  Configure the initial state and document state mapping carefully.
6.  Test every transition with separate Dispatcher and Fleet Manager
    accounts.
7.  Verify that a user cannot bypass the workflow through direct API
    calls or crafted requests.

Use a separate workflow for Maintenance Request if approval or
controlled closure is required.

### 9.6 Create workspace and reports

Create a **Fleet Operations** Workspace with shortcuts to:

-   Vehicles
-   Drivers
-   Fleet Locations
-   Trips
-   Maintenance Requests

Add dashboard charts or reports for:

-   Trips by status
-   Available vs On Trip vs Maintenance vehicles
-   Distance travelled by date range
-   Vehicle utilisation
-   Maintenance requests by status
-   Trip expense totals by type and period

Keep reports permission-aware. Avoid reports that expose driver personal
data to broad audiences.

------------------------------------------------------------------------

## 10. API and integration conventions

Frappe automatically exposes standard resource APIs for DocTypes. For
example, an authenticated client can use the resource endpoint pattern:

``` text
GET    /api/resource/Vehicle
GET    /api/resource/Vehicle/{name}
POST   /api/resource/Trip
PUT    /api/resource/Trip/{name}
```

A purpose-built method can be exposed with `@frappe.whitelist()` for
actions such as dispatch or completion. Example pattern:

``` python
import frappe


@frappe.whitelist()
def get_my_active_trips():
    # Apply explicit permission and assignment filtering.
    # Do not trust a client-supplied user identity.
    user = frappe.session.user
    return frappe.get_list(
        "Trip",
        filters={"driver_user": user, "status": "In Progress"},
        fields=["name", "vehicle", "origin", "destination", "planned_start"],
    )
```

The field `driver_user` is illustrative; add a deliberate relationship
from Driver to User if this use case is required.

### API standards

-   Use Frappe authentication mechanisms; use token authentication for
    trusted integrations and protect credentials as secrets.
-   Keep methods small, resource-oriented and permission-aware.
-   Validate all inputs server-side; never trust client-side field
    filters.
-   Prefer `frappe.get_list` when permission filtering is required.
    Understand the permission semantics before using `frappe.get_all`.
-   Do not expose unrestricted whitelisted methods or use
    `ignore_permissions=True` as a shortcut.
-   Return stable, documented response shapes and meaningful error
    messages.
-   Add API tests for unauthorised, invalid, boundary and successful
    requests.
-   Apply rate limiting and network restrictions at the appropriate
    infrastructure layer for externally exposed endpoints.
-   Version custom API contracts if mobile/external clients depend on
    them.

------------------------------------------------------------------------

## 11. Testing strategy and acceptance criteria

### Minimum test layers

  -----------------------------------------------------------------------
  Layer                               What to test
  ----------------------------------- -----------------------------------
  DocType unit tests                  Required fields, date validation,
                                      odometer calculations

  Business-rule tests                 Driver licence, vehicle
                                      eligibility, overlapping trips

  Workflow tests                      Allowed and denied transitions by
                                      role

  Permission tests                    Desk and REST access for each role

  Integration tests                   Dispatch → complete → vehicle
                                      status reconciliation

  Regression tests                    Maintenance conflict and
                                      cancellation paths

  Concurrency tests                   Two dispatch requests competing for
                                      the same vehicle/driver
  -----------------------------------------------------------------------

Use Frappe's test framework and run tests against a disposable test
site. Keep test data deterministic and avoid relying on production
records.

### POC acceptance checklist

-   [ ] Fleet Administrator can create and maintain vehicles, drivers
    and locations.
-   [ ] Dispatcher can create a trip and submit it for approval.
-   [ ] Fleet Manager can approve/reject; Dispatcher cannot approve
    their own request unless explicitly allowed by policy.
-   [ ] Inactive vehicles and drivers with expired licences cannot be
    dispatched.
-   [ ] Overlapping trips for the same vehicle or driver are rejected.
-   [ ] Dispatch captures actual start and opening odometer.
-   [ ] Completion captures actual end and closing odometer and
    calculates distance.
-   [ ] Trip expenses can be added and reported.
-   [ ] Open maintenance blocks new dispatches for the affected vehicle.
-   [ ] Vehicle status is reconciled after
    completion/cancellation/maintenance closure.
-   [ ] Users cannot access restricted records or actions through direct
    REST calls.
-   [ ] Workspace and reports provide a clear operational summary.
-   [ ] Automated tests cover critical validations and permission
    boundaries.

------------------------------------------------------------------------

## 12. Engineering standards for an organisation

### Source control and code review

-   Keep the custom app in a dedicated Git repository.
-   Use protected `main`/release branches and pull requests.
-   Require review for DocType schema changes, permission changes,
    hooks, patches and API changes.
-   Commit generated DocType JSON, Python controllers, fixtures and
    tests.
-   Do not commit site-specific configuration, database dumps, private
    files, credentials or secrets.
-   Keep commits focused and include migration/rollback considerations
    in PR descriptions.

### Code quality

-   Follow the Python style and linting conventions adopted by the
    organisation.
-   Keep business logic in controllers or domain services, not client
    scripts.
-   Avoid duplicate validation across Desk and API layers; centralise
    authoritative rules server-side.
-   Use framework APIs and ORM. Any raw SQL must be parameterised,
    reviewed and justified.
-   Avoid unnecessary `frappe.db.commit()` calls; understand the
    request/job transaction lifecycle.
-   Avoid broad exception swallowing. Log actionable context without
    leaking personal or secret data.
-   Use patches for controlled data/schema transformations; make patches
    safe to run once and review their rollback strategy.

### Security and privacy

-   Use least-privilege roles and review permissions for every DocType
    and report.
-   Treat driver licence, phone and identity data as sensitive personal
    information.
-   Use HTTPS, secure session/token handling and secret management.
-   Restrict File attachments and verify download permissions.
-   Do not log authentication tokens, personal identifiers or sensitive
    request payloads.
-   Establish retention, deletion and access-review policies before real
    personal data is loaded.
-   Keep framework and app dependencies patched; scan dependencies and
    review security advisories.

### Operations and deployment

-   Maintain separate development, staging/UAT and production sites.
-   Deploy through a repeatable CI/CD process; do not make untracked
    production Desk changes.
-   Back up database and files and periodically test restoration.
-   Run migrations during controlled releases and validate them in
    staging first.
-   Monitor application errors, background jobs, queue health, database
    capacity and scheduled jobs.
-   Document site-specific settings and keep secrets outside source
    control.
-   Define an operational owner for backup, restore, upgrades and
    incident response.

------------------------------------------------------------------------

## 13. POC delivery plan

  ------------------------------------------------------------------------
  Phase                   Work                    Exit criteria
  ----------------------- ----------------------- ------------------------
  1\. Foundation          Bench, site, app, Git   App installs cleanly on
                          repository, roles       a fresh site

  2\. Masters             Vehicle, Driver, Fleet  Master data can be
                          Location                created with validations

  3\. Trip workflow       Trip, child expenses,   Approval-to-completion
                          workflow and rules      demo succeeds

  4\. Maintenance         Maintenance Request and Maintenance prevents
                          vehicle blocking        invalid dispatch

  5\. Visibility          Workspace, reports and  Fleet Manager can review
                          dashboard               operations

  6\. Quality gate        Tests, permission       Acceptance checklist
                          review, deployment      passes on staging
                          notes                   
  ------------------------------------------------------------------------

A small team can timebox this into a short POC, but estimates should be
made after confirming the Frappe version, workflow complexity,
deployment environment and whether the POC requires scripted DocType
creation or Desk-first configuration.

------------------------------------------------------------------------

## 14. Known POC limitations and production gaps

The following must be addressed before production use:

1.  **Concurrent allocation:** Ensure vehicle/driver reservation is
    race-safe under simultaneous dispatch.
2.  **Status reconciliation:** Define a single authoritative rule for
    availability across trips and maintenance.
3.  **Multi-company/branch:** Define company, branch, cost centre and
    data-isolation requirements if applicable.
4.  **GPS and mobile:** Design device identity, location consent,
    offline sync, event ordering and conflict resolution separately.
5.  **Audit and compliance:** Confirm retention, audit evidence,
    document immutability and regulatory requirements.
6.  **Scale:** Load-test list views, reports, indexes, background queues
    and expected transaction volume.
7.  **Operational resilience:** Validate backups, restore, monitoring,
    upgrades and disaster recovery.
8.  **Financial controls:** Integrate expenses with an approved
    accounting process if financial posting is required.
9.  **Data protection:** Complete privacy/security review before using
    real driver and vehicle documents.

Do not describe the POC as production-ready until these gaps have
owners, designs and acceptance evidence.

------------------------------------------------------------------------

## 15. Demo script (10--15 minutes)

1.  Sign in as Fleet Administrator and show Vehicle, Driver and Location
    masters.
2.  Show an expired-licence driver and explain why the driver cannot be
    dispatched.
3.  Sign in as Dispatcher and create a trip for an available vehicle and
    active driver.
4.  Attempt an overlapping trip and demonstrate server-side rejection.
5.  Submit the valid trip for approval.
6.  Sign in as Fleet Manager and approve it.
7.  Dispatch the trip and enter opening odometer.
8.  Add a fuel/toll expense and complete the trip with closing odometer.
9.  Show the calculated distance and vehicle status update.
10. Create a maintenance request and demonstrate that the vehicle is
    blocked from new trips.
11. Finish on the Fleet Operations Workspace and review the reports.

### POC success measure

The POC is successful when a stakeholder can complete the full lifecycle
using Frappe Desk, see the state and audit history at each step, and
verify that invalid operations are rejected by server-side rules and
permissions.

------------------------------------------------------------------------

## 16. Official references

Use documentation matching the exact Frappe major version selected for
the POC:

-   Frappe Framework documentation: https://docs.frappe.io/framework
-   Bench documentation: https://docs.frappe.io/framework/user/en/bench
-   DocType documentation:
    https://docs.frappe.io/framework/user/en/basics/doctypes
-   REST API documentation:
    https://docs.frappe.io/framework/user/en/api/rest
-   Server Script documentation:
    https://docs.frappe.io/framework/user/en/desk/scripting/server-script
-   Hooks documentation:
    https://docs.frappe.io/framework/user/en/python-api/hooks
-   Role and permissions documentation:
    https://docs.frappe.io/framework/user/en/basics/users-and-permissions

> Documentation URLs and installation prerequisites can change between
> Frappe releases. Confirm the selected release's documentation and
> supported dependency matrix before implementation.
