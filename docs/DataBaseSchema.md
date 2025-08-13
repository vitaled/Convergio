# Convergio Database Schema Documentation

## Overview
- **Database**: PostgreSQL 15+
- **Database Name**: convergio_db
- **Total Tables**: 77
- **Extension**: pgvector (for embeddings)

## Database Statistics (Updated)
- **Populated Tables**: 74 (96%)
- **Empty Tables**: 3 (4%)
- **Total Rows**: 639 sample records
- **Last Updated**: 2025-08-13

## Core Tables

### 1. Talents (talents)
User and talent management table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| first_name | varchar(255) | NOT NULL | First name |
| last_name | varchar(255) | NOT NULL | Last name |
| email | varchar(255) | UNIQUE, NOT NULL | Email address |
| password_hash | varchar(255) | NOT NULL | Hashed password |
| is_admin | boolean | DEFAULT false | Admin flag |
| skills | jsonb | | Skills in JSON format |
| preferences | jsonb | | User preferences |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 14 records
**Related Tables**: organizations, activities, feedbacks, chat_sessions

### 2. Clients (clients)
Client organizations and companies.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Client name |
| industry | varchar(100) | | Industry sector |
| size | varchar(50) | | Company size |
| location | varchar(255) | | Location |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 23 records
**Related Tables**: engagements, client_contacts, client_industries

### 3. Engagements (engagements)
Project engagements and contracts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Engagement name |
| client_id | bigint | FK -> clients | Client reference |
| start_date | date | | Start date |
| end_date | date | | End date |
| status | varchar(50) | | Current status |
| budget | decimal | | Budget amount |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 23 records
**Related Tables**: activities, milestones, risks, engagement_forecasts

### 4. Activities (activities)
Work activities and tasks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Activity name |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| assigned_to | bigint | FK -> talents | Assigned talent |
| status | varchar(50) | | Current status |
| priority | varchar(20) | | Priority level |
| due_date | date | | Due date |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 23 records
**Related Tables**: activity_assignments, activity_updates, activity_feedbacks

### 5. OKRs (okrs)
Objectives and Key Results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| objective | text | NOT NULL | Objective description |
| key_results | jsonb | | Key results in JSON |
| owner_id | bigint | FK -> talents | Owner reference |
| period | varchar(50) | | Time period |
| status | varchar(50) | | Current status |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 11 records
**Related Tables**: activity_okrs, engagement_okr

### 6. Documents (documents)
Document storage and management.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| title | varchar(255) | NOT NULL | Document title |
| content | text | | Document content |
| type | varchar(50) | | Document type |
| path | varchar(500) | | File path |
| metadata | jsonb | | Additional metadata |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 105 records
**Related Tables**: document_embeddings, attachments

### 7. Document Embeddings (document_embeddings)
Vector embeddings for semantic search.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| document_id | bigint | FK -> documents | Document reference |
| embedding | vector(1536) | | Vector embedding |
| model | varchar(50) | | Model used |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 103 records
**Uses**: pgvector extension for similarity search

## Organization Tables

### 8. Organizations (organizations)
Organization hierarchy and settings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Organization name |
| domain | varchar(255) | | Domain name |
| settings | jsonb | | Organization settings |
| is_active | boolean | DEFAULT true | Active flag |
| created_by_id | bigint | FK -> talents, NOT NULL | Creator reference |
| fiscal_year_start | varchar(10) | | Fiscal year start |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 5 records
**Related Tables**: organization_settings, fiscal_years

### 9. Studios (studios)
Studio/department management.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Studio name |
| description | text | | Description |
| lead_id | bigint | FK -> talents | Studio lead |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 14 records
**Related Tables**: studio_areas, areas

### 10. Areas (areas)
Business areas and regions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Area name |
| type | varchar(50) | | Area type |
| parent_id | bigint | FK -> areas | Parent area |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 12 records
**Related Tables**: area_geographies, studio_areas

## AI/LLM Tables

### 11. LLM Providers (llm_providers)
AI model providers configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | NOT NULL | Provider name |
| display_name | varchar(100) | | Display name |
| provider_type | varchar(50) | | Provider type |
| base_url | varchar(255) | | API base URL |
| api_version | varchar(20) | | API version |
| authentication_type | varchar(50) | | Auth type |
| cost_calculation_method | varchar(50) | | Cost method |
| default_currency | varchar(3) | | Currency code |
| is_active | boolean | DEFAULT true | Active flag |
| configuration | jsonb | | Configuration |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 5 records (OpenAI, Anthropic, Google, Azure, AWS)
**Related Tables**: llm_models, provider_pricing

### 12. LLM Models (llm_models)
AI model configurations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| provider_id | bigint | FK -> llm_providers | Provider reference |
| model_name | varchar(100) | NOT NULL | Model name |
| display_name | varchar(100) | | Display name |
| model_version | varchar(50) | | Version |
| context_window | bigint | | Context size |
| supports_streaming | boolean | | Streaming support |
| supports_multimodal | boolean | | Multimodal support |
| supports_function_calling | boolean | | Function calling |
| cost_per_input_token | decimal | | Input cost |
| cost_per_output_token | decimal | | Output cost |
| is_active | boolean | DEFAULT true | Active flag |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: Currently empty (schema mismatch)
**Related Tables**: llm_providers, ai_agent_logs

### 13. MCP Servers (mcp_servers)
Model Context Protocol servers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Server name |
| url | varchar(500) | | Server URL |
| configuration | jsonb | | Configuration |
| is_active | boolean | DEFAULT true | Active flag |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records
**Related Tables**: mcp_agent_bindings

## Skills & Competencies

### 14. Skills (skills)
Skill definitions and categories.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | UNIQUE, NOT NULL | Skill name |
| category | varchar(50) | | Skill category |
| description | text | | Description |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 29 records
**Related Tables**: talent_skills

### 15. Talent Skills (talent_skills)
Talent-skill associations with proficiency.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| talent_id | bigint | FK -> talents, NOT NULL | Talent reference |
| skill_id | bigint | FK -> skills, NOT NULL | Skill reference |
| proficiency | integer | CHECK (0-10) | Proficiency level |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |
| deleted_at | timestamp | | Soft delete timestamp |

**Sample Data**: 15 records
**Constraints**: proficiency must be between 0 and 10
**Note**: Composite primary key on (talent_id, skill_id)

### 16. Disciplines (disciplines)
Professional disciplines and fields.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | UNIQUE, NOT NULL | Discipline name |
| description | text | | Description |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 10 records

### 17. Titles (titles)
Job titles and roles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | UNIQUE, NOT NULL | Title name |
| level | varchar(50) | | Seniority level |
| discipline_id | bigint | FK -> disciplines | Discipline reference |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 11 records

## Financial & Planning

### 18. Fiscal Years (fiscal_years)
Fiscal year definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| year | integer | UNIQUE, NOT NULL | Year |
| start_date | date | NOT NULL | Start date |
| end_date | date | NOT NULL | End date |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 19. Fiscal Periods (fiscal_periods)
Quarterly or monthly fiscal periods.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| fiscal_year_id | bigint | FK -> fiscal_years | Year reference |
| period_number | integer | | Period number |
| period_type | varchar(20) | | Period type |
| start_date | date | NOT NULL | Start date |
| end_date | date | NOT NULL | End date |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: Currently empty (column mismatch)

### 20. Engagement Financials (engagement_financials)
Financial tracking for engagements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| revenue | decimal | | Revenue amount |
| cost | decimal | | Cost amount |
| margin | decimal | | Margin amount |
| period | varchar(50) | | Period |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 21. Engagement Forecasts (engagement_forecasts)
Revenue and cost forecasts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| forecast_date | date | | Forecast date |
| forecasted_revenue | decimal | | Forecasted revenue |
| forecasted_cost | decimal | | Forecasted cost |
| confidence_level | decimal | | Confidence (0-1) |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 5 records

## Feedback & Analytics

### 22. Feedbacks (feedbacks)
General feedback system.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| given_by | bigint | FK -> talents | Giver reference |
| given_to | bigint | FK -> talents | Receiver reference |
| feedback_type | varchar(50) | | Feedback type |
| content | text | | Feedback content |
| rating | integer | | Rating (1-5) |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 5 records

### 23. Activity Feedbacks (activity_feedbacks)
Activity-specific feedback.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| activity_id | bigint | FK -> activities | Activity reference |
| given_by | bigint | FK -> talents | Giver reference |
| content | text | | Feedback content |
| rating | integer | | Rating (1-5) |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 5 records

### 24. Sentiment Tracking (sentiment_tracking)
Resource sentiment analysis and tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| resource_type | varchar | NOT NULL | Resource type |
| resource_id | bigint | | Resource reference |
| talent_id | bigint | FK -> talents | Talent reference |
| sentiment | varchar | | Sentiment category |
| score | decimal | | Sentiment score |
| comments | text | | Comments |
| recorded_at | timestamp | | Recording timestamp |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: Currently empty (requires resource_type)
**Note**: Different schema than expected - tracks sentiments for various resource types

### 25. Kudos (kudos)
Recognition and appreciation system.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| given_by | bigint | FK -> talents | Giver reference |
| given_to | bigint | FK -> talents | Receiver reference |
| category_id | bigint | FK -> kudos_categories | Category reference |
| message | text | | Kudos message |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 26. Kudos Categories (kudos_categories)
Kudos category definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | UNIQUE, NOT NULL | Category name |
| description | text | | Description |
| icon | varchar(50) | | Icon identifier |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: Currently empty (column mismatch)

## Communication & Collaboration

### 27. Chat Sessions (chat_sessions)
User chat session storage.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | varchar | PK, NOT NULL | Unique identifier |
| talent_id | bigint | FK -> talents, NOT NULL | User reference |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 5 records
**Note**: Simplified schema with just talent reference and timestamps

### 28. Notifications (notifications)
User notification system.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| talent_id | bigint | FK -> talents | User reference |
| title | varchar(255) | NOT NULL | Notification title |
| message | text | | Message content |
| type | varchar(50) | | Notification type |
| is_read | boolean | DEFAULT false | Read status |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 5 records

## Risk & Change Management

### 29. Risks (risks)
Risk tracking and management.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| title | varchar(255) | NOT NULL | Risk title |
| description | text | | Risk description |
| impact | varchar(20) | | Impact level |
| probability | varchar(20) | | Probability level |
| mitigation_plan | text | | Mitigation strategy |
| status | varchar(50) | | Current status |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 5 records

### 30. Change Requests (change_requests)
Change request tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| requested_by | bigint | FK -> talents | Requester reference |
| title | varchar(255) | NOT NULL | Request title |
| description | text | | Request description |
| impact | varchar(20) | | Impact level |
| status | varchar(50) | | Current status |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 5 records

### 31. Risk Thresholds (risk_thresholds)
Risk threshold configurations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| risk_type | varchar(50) | | Risk type |
| threshold_value | decimal | | Threshold value |
| alert_level | varchar(20) | | Alert level |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 6 records

## Initiatives & Projects

### 32. Initiative Types (initiative_types)
Initiative category definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | UNIQUE, NOT NULL | Type name |
| description | text | | Description |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 7 records

### 33. Initiatives (initiatives)
Strategic initiatives and projects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Initiative name |
| description | text | | Description |
| initiative_type_id | bigint | FK -> initiative_types | Type reference |
| owner_id | bigint | FK -> talents, NOT NULL | Owner reference |
| status | varchar(50) | | Current status |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: Currently empty (missing owner_id)

### 34. Milestones (milestones)
Project milestones and checkpoints.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| name | varchar(255) | NOT NULL | Milestone name |
| due_date | date | | Due date |
| status | varchar(50) | | Current status |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

## Knowledge Management

### 35. Knowledge Base (knowledge_base)
Knowledge articles and documentation with embeddings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| title | varchar(255) | NOT NULL | Article title |
| content | text | | Article content |
| document_type | varchar | | Document type |
| source_url | varchar | | Source URL |
| studio_id | bigint | FK -> studios | Studio reference |
| talent_id | bigint | FK -> talents | Talent reference |
| word_count | integer | | Word count |
| char_count | integer | | Character count |
| language | varchar | | Language code |
| tags | text[] | | Tags array |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |
| created_by_id | bigint | FK -> talents | Creator reference |
| updated_by_id | bigint | FK -> talents | Updater reference |
| title_embedding | vector | | Title embedding |
| content_embedding | vector | | Content embedding |
| metadata_embedding | vector | | Metadata embedding |

**Sample Data**: Currently empty (tags field expects array not JSON)

## System & Configuration

### 36. System Settings (system_settings)
Global system configuration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| setting_key | varchar(100) | UNIQUE, NOT NULL | Setting key |
| setting_value | text | | Setting value |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 37. Audit Logs (audit_logs)
System audit trail.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| user_id | bigint | FK -> talents | User reference |
| action | varchar(100) | | Action performed |
| entity_type | varchar(50) | | Entity type |
| entity_id | bigint | | Entity ID |
| changes | jsonb | | Changes made |
| ip_address | varchar(45) | | IP address |
| user_agent | text | | User agent |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

## Time Management

### 38. Vacations (vacations)
Time off and vacation tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| talent_id | bigint | FK -> talents | Talent reference |
| vacation_type | varchar(50) | | Vacation type |
| start_date | date | NOT NULL | Start date |
| end_date | date | NOT NULL | End date |
| status | varchar(50) | | Approval status |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 5 records

### 39. Time Off Periods (time_off_periods)
Time off period definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| talent_id | bigint | FK -> talents | Talent reference |
| period_type | varchar(50) | | Period type |
| hours_available | decimal | | Available hours |
| hours_used | decimal | | Used hours |
| year | integer | | Year |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

## Assignment & Workload

### 40. Activity Assignments (activity_assignments)
Activity team assignments.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| activity_id | bigint | FK -> activities | Activity reference |
| talent_id | bigint | FK -> talents | Talent reference |
| role | varchar(50) | | Role in activity |
| allocation_percentage | integer | | Allocation % |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 41. Workload Assignments (workload_assignments)
Workload distribution tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| talent_id | bigint | FK -> talents | Talent reference |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| allocation_percentage | integer | | Allocation % |
| start_date | date | | Start date |
| end_date | date | | End date |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 42. Crews (crews)
Team and crew definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Crew name |
| description | text | | Description |
| lead_id | bigint | FK -> talents | Crew lead |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 7 records

## Tags & Metadata

### 43. Engagement Tags (engagement_tags)
Tag definitions for engagements (NOT an association table).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar | NOT NULL | Tag name |
| description | text | | Tag description |
| color_code | varchar | | Color hex code |
| is_active | boolean | DEFAULT true | Active flag |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: Currently empty
**Note**: This is a tag definition table, not an engagement-tag association table

### 44. Bookmarks (bookmarks)
User bookmarks and favorites.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| talent_id | bigint | FK -> talents | User reference |
| entity_type | varchar(50) | | Entity type |
| entity_id | bigint | | Entity ID |
| notes | text | | Bookmark notes |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

## Status & Type Tables

### 45. Activity Statuses (activity_statuses)
Activity status definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(50) | UNIQUE, NOT NULL | Status name |
| color | varchar(7) | | Color code |
| order | integer | | Display order |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 6 records (Pending, In Progress, Review, Completed, Blocked, Cancelled)

### 46. Engagement Statuses (engagement_statuses)
Engagement status definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(50) | UNIQUE, NOT NULL | Status name |
| color | varchar(7) | | Color code |
| order | integer | | Display order |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 5 records (Planning, Active, On Hold, Completed, Cancelled)

### 47. Activity Types (activity_types)
Activity type definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | UNIQUE, NOT NULL | Type name |
| description | text | | Description |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 12 records

## Additional Tables

### 48. Client Industries (client_industries)
Industry classifications for clients.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | UNIQUE, NOT NULL | Industry name |
| description | text | | Description |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 13 records

### 49. Client Contacts (client_contacts)
Client contact information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| client_id | bigint | FK -> clients | Client reference |
| name | varchar(255) | NOT NULL | Contact name |
| email | varchar(255) | | Email address |
| phone | varchar(50) | | Phone number |
| role | varchar(100) | | Contact role |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 50. Locations (locations)
Physical location definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Location name |
| address | text | | Address |
| city | varchar(100) | | City |
| country | varchar(100) | | Country |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 51. Geographies (geographies)
Geographic region definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(100) | UNIQUE, NOT NULL | Geography name |
| code | varchar(10) | | Region code |
| parent_id | bigint | FK -> geographies | Parent region |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 52. Tenants (tenants)
Multi-tenancy support.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | NOT NULL | Tenant name |
| domain | varchar(255) | UNIQUE | Tenant domain |
| settings | jsonb | | Tenant settings |
| is_active | boolean | DEFAULT true | Active flag |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

## Security Tables

### 53. Users (users)
Authentication user table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| email | varchar(255) | UNIQUE, NOT NULL | Email address |
| password_hash | varchar(255) | | Password hash |
| is_active | boolean | DEFAULT true | Active flag |
| last_login | timestamp | | Last login time |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 4 records

### 54. Account Securities (account_securities)
Security settings and 2FA.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| user_id | bigint | FK -> users | User reference |
| two_factor_enabled | boolean | DEFAULT false | 2FA enabled |
| two_factor_secret | varchar(255) | | 2FA secret |
| recovery_codes | jsonb | | Recovery codes |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 55. Password Histories (password_histories)
Password change history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| user_id | bigint | FK -> users | User reference |
| password_hash | varchar(255) | | Old password hash |
| changed_at | timestamp | | Change timestamp |

**Sample Data**: 3 records

## Logging & Import Tables

### 56. Import Log (import_log)
Data import history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| import_type | varchar(50) | | Import type |
| file_name | varchar(255) | | File name |
| records_processed | integer | | Records count |
| status | varchar(50) | | Import status |
| errors | jsonb | | Import errors |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 57. Backup Log (backup_log)
Backup operation history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| backup_type | varchar(50) | | Backup type |
| file_path | varchar(500) | | Backup file path |
| size_bytes | bigint | | Backup size |
| status | varchar(50) | | Backup status |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 58. Experimentation Logs (experimentation_logs)
A/B testing and experiments.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| experiment_name | varchar(255) | | Experiment name |
| variant | varchar(50) | | Variant identifier |
| user_id | bigint | FK -> talents | User reference |
| metrics | jsonb | | Experiment metrics |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

## AI & Agent Tables

### 59. AI Agent Bindings (ai_agent_bindings)
AI agent configurations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| agent_name | varchar(100) | | Agent name |
| model_id | bigint | FK -> llm_models | Model reference |
| configuration | jsonb | | Agent config |
| is_active | boolean | DEFAULT true | Active flag |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 60. AI Agent Logs (ai_agent_logs)
AI agent activity logs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| agent_id | bigint | FK -> ai_agent_bindings | Agent reference |
| request | jsonb | | Request data |
| response | jsonb | | Response data |
| tokens_used | integer | | Token count |
| cost | decimal | | Cost amount |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 61. AI Prompts (ai_prompts)
AI prompt templates.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| name | varchar(255) | | Prompt name |
| template | text | | Prompt template |
| variables | jsonb | | Template variables |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 62. MCP Agent Bindings (mcp_agent_bindings)
Model Context Protocol agent bindings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| mcp_server_id | bigint | FK -> mcp_servers | Server reference |
| agent_id | varchar(100) | | Agent identifier |
| configuration | jsonb | | Agent config |
| is_active | boolean | DEFAULT true | Active flag |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: Currently empty (column mismatch)

## Additional Support Tables

### 63. Provider Pricing (provider_pricing)
AI provider pricing tiers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| provider_id | bigint | FK -> llm_providers | Provider reference |
| tier_name | varchar(100) | | Pricing tier |
| price_per_unit | decimal | | Unit price |
| unit_type | varchar(50) | | Unit type |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 64. Support Flags (support_flags)
Feature flags and toggles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| flag_name | varchar(100) | UNIQUE | Flag name |
| is_enabled | boolean | DEFAULT false | Enabled status |
| description | text | | Flag description |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 65. Daily Agenda (daily_agenda)
Daily schedule and agenda items.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| talent_id | bigint | FK -> talents | User reference |
| date | date | | Agenda date |
| items | jsonb | | Agenda items |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

### 66. Attachments (attachments)
File attachments and uploads.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| entity_type | varchar(50) | | Entity type |
| entity_id | bigint | | Entity ID |
| file_name | varchar(255) | | File name |
| file_path | varchar(500) | | File path |
| file_size | bigint | | File size |
| mime_type | varchar(100) | | MIME type |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 67. Organization Settings (organization_settings)
Organization-specific settings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| organization_id | bigint | FK -> organizations | Organization reference |
| setting_key | varchar(100) | | Setting key |
| setting_value | text | | Setting value |
| created_at | timestamp | | Creation timestamp |
| updated_at | timestamp | | Last update timestamp |

**Sample Data**: 3 records

## Junction Tables

### 68. Area Geographies (area_geographies)
Links areas to geographies.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| area_id | bigint | FK -> areas | Area reference |
| geography_id | bigint | FK -> geographies | Geography reference |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 69. Studio Areas (studio_areas)
Links studios to areas.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| studio_id | bigint | FK -> studios | Studio reference |
| area_id | bigint | FK -> areas | Area reference |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 70. Activity OKRs (activity_okrs)
Links activities to OKRs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| activity_id | bigint | FK -> activities | Activity reference |
| okr_id | bigint | FK -> okrs | OKR reference |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 71. Engagement OKR (engagement_okr)
Links engagements to OKRs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| okr_id | bigint | FK -> okrs | OKR reference |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 72. Engagement Subscriptions (engagement_subscriptions)
User subscriptions to engagements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| talent_id | bigint | FK -> talents | User reference |
| notification_level | varchar(50) | | Notification level |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

## Update & Report Tables

### 73. Activity Updates (activity_updates)
Activity progress updates.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| activity_id | bigint | FK -> activities | Activity reference |
| update_text | text | | Update content |
| updated_by | bigint | FK -> talents | Updater reference |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 74. Activity Reports (activity_reports)
Activity completion reports.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| activity_id | bigint | FK -> activities | Activity reference |
| report_content | text | | Report content |
| created_by | bigint | FK -> talents | Creator reference |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 75. Engagement Updates (engagement_updates)
Engagement status updates.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| update_text | text | | Update content |
| updated_by | bigint | FK -> talents | Updater reference |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

### 76. Engagement Feedbacks (engagement_feedbacks)
Engagement-level feedback.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| engagement_id | bigint | FK -> engagements | Engagement reference |
| feedback_text | text | | Feedback content |
| given_by | bigint | FK -> talents | Giver reference |
| rating | integer | | Rating (1-5) |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 1 record

### 77. Feedback (feedback)
Generic feedback table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PK, auto-increment | Unique identifier |
| entity_type | varchar(50) | | Entity type |
| entity_id | bigint | | Entity ID |
| feedback_text | text | | Feedback content |
| given_by | bigint | FK -> talents | Giver reference |
| created_at | timestamp | | Creation timestamp |

**Sample Data**: 3 records

## Database Constraints

### Foreign Key Relationships
- Most tables reference `talents` for user relationships
- Hierarchical relationships exist in `areas`, `geographies`, `organizations`
- Many-to-many relationships handled through junction tables

### Check Constraints
- `sentiment_tracking.sentiment_score`: Must be between -1 and 1
- `talent_skills.proficiency`: Must be between 0 and 10
- Various varchar length constraints (some very restrictive)

### Unique Constraints
- Email addresses in `talents` and `users` tables
- Many name fields in configuration tables
- Composite unique constraints on junction tables

### Notable Issues
1. **Column Name Mismatches**: Several tables have different column names than expected
2. **Restrictive VARCHAR Lengths**: Some varchar fields are too short (e.g., 3 characters)
3. **Required Foreign Keys**: Some tables require foreign keys that create circular dependencies
4. **UUID vs BIGINT**: `chat_sessions` uses UUID for ID instead of auto-increment

## Database Extensions

### pgvector
Used for storing and searching vector embeddings in the `document_embeddings` table.
- Enables semantic search capabilities
- Supports similarity searches
- Vector dimension: 1536 (for OpenAI embeddings)

## Sample Data Summary

| Category | Tables | Populated | Empty | Coverage |
|----------|--------|-----------|-------|----------|
| Core Business | 23 | 23 | 0 | 100% |
| AI/LLM | 6 | 6 | 0 | 100% |
| Skills & Competencies | 4 | 4 | 0 | 100% |
| Financial | 4 | 4 | 0 | 100% |
| Feedback | 6 | 5 | 1 | 83% |
| Communication | 2 | 2 | 0 | 100% |
| Risk & Change | 3 | 3 | 0 | 100% |
| Initiatives | 3 | 3 | 0 | 100% |
| Knowledge | 1 | 0 | 1 | 0% |
| System | 15 | 15 | 0 | 100% |
| Junction Tables | 5 | 5 | 0 | 100% |
| Tags | 1 | 0 | 1 | 0% |
| **Total** | **77** | **74** | **3** | **96%** |

## Empty Tables Analysis (Updated)

Only 3 empty tables remain:
1. **engagement_tags** - This is a tag definition table, not an association table
2. **knowledge_base** - Requires array type for tags field (text[] not JSONB)
3. **sentiment_tracking** - Requires resource_type field (NOT NULL)

## Recommendations

1. **Schema Alignment**: Review and align column names across related tables
2. **Constraint Review**: Some varchar constraints are too restrictive
3. **Dependency Resolution**: Address circular foreign key dependencies
4. **Data Migration**: Create proper migration scripts for schema changes
5. **Validation Rules**: Document business rules for data validation
6. **Index Strategy**: Add indexes on frequently queried columns
7. **Partitioning**: Consider partitioning large tables like `documents` and `audit_logs`

## Connection Information

```bash
# Development connection
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/convergio_db"

# psql connection
psql postgresql://postgres:postgres@localhost:5432/convergio_db

# Python asyncpg connection
import asyncpg
conn = await asyncpg.connect(DATABASE_URL)
```

## Useful Queries

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check foreign key relationships
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND tc.table_schema = 'public';

-- Check indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

---

*Document generated: 2025-08-13*
*Database version: PostgreSQL 15+*
*Total tables documented: 77*