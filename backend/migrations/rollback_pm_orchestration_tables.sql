-- =====================================================
-- Rollback PM Orchestration Database Migration
-- Removes tables and objects created for AI orchestration
-- =====================================================

-- WARNING: This will permanently delete all orchestration data
-- Only run this if you need to completely remove the orchestration system

BEGIN;

-- =====================================================
-- Drop views first (due to dependencies)
-- =====================================================

DROP VIEW IF EXISTS agent_performance;
DROP VIEW IF EXISTS journey_progress;
DROP VIEW IF EXISTS active_orchestrations;

-- =====================================================
-- Drop triggers
-- =====================================================

DROP TRIGGER IF EXISTS update_agent_collaboration_metrics_updated_at ON agent_collaboration_metrics;
DROP TRIGGER IF EXISTS update_project_conversations_updated_at ON project_conversations;
DROP TRIGGER IF EXISTS update_project_touchpoints_updated_at ON project_touchpoints;
DROP TRIGGER IF EXISTS update_project_journey_stages_updated_at ON project_journey_stages;
DROP TRIGGER IF EXISTS update_project_agent_assignments_updated_at ON project_agent_assignments;
DROP TRIGGER IF EXISTS update_project_orchestrations_updated_at ON project_orchestrations;

-- =====================================================
-- Drop tables (in reverse dependency order)
-- =====================================================

DROP TABLE IF EXISTS agent_collaboration_metrics;
DROP TABLE IF EXISTS project_conversations;
DROP TABLE IF EXISTS project_touchpoints;
DROP TABLE IF EXISTS project_journey_stages;
DROP TABLE IF EXISTS project_agent_assignments;
DROP TABLE IF EXISTS project_orchestrations;

-- =====================================================
-- Drop enums
-- =====================================================

DROP TYPE IF EXISTS agent_role;
DROP TYPE IF EXISTS touchpoint_type;
DROP TYPE IF EXISTS journey_stage;
DROP TYPE IF EXISTS coordination_pattern;
DROP TYPE IF EXISTS orchestration_status;

-- =====================================================
-- Drop trigger function
-- =====================================================

DROP FUNCTION IF EXISTS update_updated_at_column();

-- Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'PM Orchestration tables and objects removed successfully at %', NOW();
    RAISE WARNING 'All orchestration data has been permanently deleted!';
END
$$;

COMMIT;