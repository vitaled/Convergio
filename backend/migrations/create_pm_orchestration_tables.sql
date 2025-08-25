-- =====================================================
-- Enhanced PM Orchestration Database Migration
-- Creates tables for AI-orchestrated project management
-- =====================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Enums for orchestration system
-- =====================================================

CREATE TYPE orchestration_status AS ENUM (
    'initializing',
    'active', 
    'paused',
    'optimizing',
    'completed',
    'failed'
);

CREATE TYPE coordination_pattern AS ENUM (
    'hierarchical',
    'parallel',
    'sequential', 
    'swarm',
    'hybrid'
);

CREATE TYPE journey_stage AS ENUM (
    'discovery',
    'planning',
    'execution',
    'validation',
    'delivery',
    'closure'
);

CREATE TYPE touchpoint_type AS ENUM (
    'agent_interaction',
    'client_checkin',
    'milestone_review',
    'status_update',
    'decision_point',
    'quality_gate',
    'escalation'
);

CREATE TYPE agent_role AS ENUM (
    'primary',
    'contributor',
    'consultant', 
    'reviewer',
    'observer'
);

-- =====================================================
-- Main orchestration table
-- =====================================================

CREATE TABLE project_orchestrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Orchestration configuration
    orchestration_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    primary_agent VARCHAR(100) NOT NULL,
    coordination_pattern coordination_pattern DEFAULT 'hierarchical',
    auto_agent_assignment BOOLEAN DEFAULT TRUE,
    real_time_monitoring BOOLEAN DEFAULT TRUE,
    
    -- Current state
    orchestration_status orchestration_status DEFAULT 'initializing',
    current_stage journey_stage DEFAULT 'discovery',
    active_conversation_id VARCHAR(255),
    
    -- Performance metrics
    ai_efficiency_score FLOAT DEFAULT 0.0 CHECK (ai_efficiency_score >= 0 AND ai_efficiency_score <= 1),
    agent_collaboration_score FLOAT DEFAULT 0.0 CHECK (agent_collaboration_score >= 0 AND agent_collaboration_score <= 1),
    cost_per_deliverable FLOAT DEFAULT 0.0,
    optimization_score FLOAT DEFAULT 0.0,
    
    -- Journey tracking
    journey_start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    stage_progression JSONB DEFAULT '[]',
    touchpoint_count INTEGER DEFAULT 0,
    satisfaction_score FLOAT DEFAULT 0.0 CHECK (satisfaction_score >= 0 AND satisfaction_score <= 1),
    
    -- Configuration and context
    orchestration_config JSONB DEFAULT '{}',
    context_data JSONB DEFAULT '{}',
    constraints JSONB DEFAULT '[]',
    success_criteria JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_optimization TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(project_id)
);

-- =====================================================
-- Agent assignments table
-- =====================================================

CREATE TABLE project_agent_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchestration_id UUID NOT NULL REFERENCES project_orchestrations(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    agent_role agent_role DEFAULT 'contributor',
    
    -- Assignment details
    assignment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assignment_reason TEXT,
    expected_contribution TEXT,
    active BOOLEAN DEFAULT TRUE,
    
    -- Performance tracking
    tasks_completed INTEGER DEFAULT 0,
    tasks_assigned INTEGER DEFAULT 0,
    efficiency_score FLOAT DEFAULT 0.0 CHECK (efficiency_score >= 0 AND efficiency_score <= 1),
    collaboration_score FLOAT DEFAULT 0.0 CHECK (collaboration_score >= 0 AND collaboration_score <= 1),
    quality_score FLOAT DEFAULT 0.0 CHECK (quality_score >= 0 AND quality_score <= 1),
    
    -- Cost tracking
    cost_incurred FLOAT DEFAULT 0.0,
    tokens_used INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    
    -- Agent-specific configuration
    agent_config JSONB DEFAULT '{}',
    tools_enabled JSONB DEFAULT '[]',
    permissions JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- Journey stages table
-- =====================================================

CREATE TABLE project_journey_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchestration_id UUID NOT NULL REFERENCES project_orchestrations(id) ON DELETE CASCADE,
    stage_name journey_stage NOT NULL,
    stage_order INTEGER NOT NULL,
    
    -- Stage execution details
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    estimated_duration_days INTEGER,
    actual_duration_days INTEGER,
    
    -- Status and progress
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'blocked', 'skipped')),
    progress_percentage FLOAT DEFAULT 0.0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    completion_confidence FLOAT DEFAULT 0.0,
    
    -- Agent involvement
    primary_agents JSONB DEFAULT '[]',
    contributing_agents JSONB DEFAULT '[]',
    agent_interactions INTEGER DEFAULT 0,
    
    -- Deliverables and outcomes
    expected_deliverables JSONB DEFAULT '[]',
    actual_deliverables JSONB DEFAULT '[]',
    deliverable_quality_score FLOAT DEFAULT 0.0,
    
    -- Quality and satisfaction metrics
    satisfaction_score FLOAT DEFAULT 0.0 CHECK (satisfaction_score >= 0 AND satisfaction_score <= 1),
    efficiency_score FLOAT DEFAULT 0.0 CHECK (efficiency_score >= 0 AND efficiency_score <= 1),
    cost_efficiency FLOAT DEFAULT 0.0,
    
    -- Issues and risks
    blockers JSONB DEFAULT '[]',
    risks_identified JSONB DEFAULT '[]',
    mitigation_actions JSONB DEFAULT '[]',
    
    -- Metadata
    stage_notes TEXT,
    lessons_learned TEXT,
    improvement_suggestions JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(orchestration_id, stage_name)
);

-- =====================================================
-- Touchpoints table (CRM-style interaction tracking)
-- =====================================================

CREATE TABLE project_touchpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchestration_id UUID NOT NULL REFERENCES project_orchestrations(id) ON DELETE CASCADE,
    touchpoint_type touchpoint_type NOT NULL,
    
    -- Interaction details
    initiated_by VARCHAR(100) NOT NULL,
    participants JSONB DEFAULT '[]',
    interaction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_minutes INTEGER,
    channel VARCHAR(50),
    
    -- Content and context
    title VARCHAR(500),
    summary TEXT,
    key_decisions JSONB DEFAULT '[]',
    action_items JSONB DEFAULT '[]',
    follow_up_required BOOLEAN DEFAULT FALSE,
    
    -- Sentiment and quality
    sentiment_score FLOAT DEFAULT 0.0 CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    satisfaction_score FLOAT DEFAULT 0.0 CHECK (satisfaction_score >= 0 AND satisfaction_score <= 1),
    productivity_score FLOAT DEFAULT 0.0 CHECK (productivity_score >= 0 AND productivity_score <= 1),
    
    -- Relationships and references
    related_stage journey_stage,
    related_tasks JSONB DEFAULT '[]',
    related_agents JSONB DEFAULT '[]',
    
    -- Impact and outcomes
    impact_level VARCHAR(20) DEFAULT 'medium' CHECK (impact_level IN ('low', 'medium', 'high', 'critical')),
    outcomes_achieved JSONB DEFAULT '[]',
    issues_raised JSONB DEFAULT '[]',
    
    -- Metadata
    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Conversation tracking table
-- =====================================================

CREATE TABLE project_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchestration_id UUID NOT NULL REFERENCES project_orchestrations(id) ON DELETE CASCADE,
    conversation_id VARCHAR(255) NOT NULL,
    
    -- Conversation metadata
    topic VARCHAR(500),
    purpose VARCHAR(100),
    participants JSONB DEFAULT '[]',
    
    -- Status and progress
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'terminated')),
    message_count INTEGER DEFAULT 0,
    turn_count INTEGER DEFAULT 0,
    
    -- Performance metrics
    efficiency_score FLOAT DEFAULT 0.0 CHECK (efficiency_score >= 0 AND efficiency_score <= 1),
    collaboration_quality FLOAT DEFAULT 0.0 CHECK (collaboration_quality >= 0 AND collaboration_quality <= 1),
    outcome_quality FLOAT DEFAULT 0.0 CHECK (outcome_quality >= 0 AND outcome_quality <= 1),
    
    -- Cost tracking
    total_cost FLOAT DEFAULT 0.0,
    tokens_used INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    
    -- Outcomes and deliverables
    decisions_made JSONB DEFAULT '[]',
    action_items JSONB DEFAULT '[]',
    deliverables_produced JSONB DEFAULT '[]',
    issues_resolved JSONB DEFAULT '[]',
    
    -- Timing
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    conversation_summary TEXT,
    key_insights JSONB DEFAULT '[]',
    improvement_suggestions JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Agent collaboration metrics table
-- =====================================================

CREATE TABLE agent_collaboration_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchestration_id UUID NOT NULL REFERENCES project_orchestrations(id) ON DELETE CASCADE,
    
    -- Agent pair or group
    primary_agent VARCHAR(100) NOT NULL,
    secondary_agent VARCHAR(100),
    agent_group JSONB DEFAULT '[]',
    
    -- Collaboration metrics
    interaction_frequency FLOAT DEFAULT 0.0,
    synergy_score FLOAT DEFAULT 0.0 CHECK (synergy_score >= 0 AND synergy_score <= 1),
    conflict_score FLOAT DEFAULT 0.0 CHECK (conflict_score >= 0 AND conflict_score <= 1),
    efficiency_multiplier FLOAT DEFAULT 1.0,
    
    -- Performance outcomes
    joint_tasks_completed INTEGER DEFAULT 0,
    average_task_quality FLOAT DEFAULT 0.0 CHECK (average_task_quality >= 0 AND average_task_quality <= 1),
    collaboration_duration_hours FLOAT DEFAULT 0.0,
    
    -- Analysis period
    measurement_start TIMESTAMP WITH TIME ZONE NOT NULL,
    measurement_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Insights and recommendations
    collaboration_insights JSONB DEFAULT '[]',
    optimization_suggestions JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Indexes for performance
-- =====================================================

-- Project orchestrations indexes
CREATE INDEX idx_project_orchestration_status ON project_orchestrations(orchestration_status);
CREATE INDEX idx_project_orchestration_stage ON project_orchestrations(current_stage);
CREATE INDEX idx_project_orchestration_agent ON project_orchestrations(primary_agent);
CREATE INDEX idx_project_orchestration_created ON project_orchestrations(created_at);

-- Agent assignments indexes
CREATE INDEX idx_agent_assignment_orchestration ON project_agent_assignments(orchestration_id);
CREATE INDEX idx_agent_assignment_name ON project_agent_assignments(agent_name);
CREATE INDEX idx_agent_assignment_role ON project_agent_assignments(agent_role);
CREATE INDEX idx_agent_assignment_active ON project_agent_assignments(active);

-- Journey stages indexes
CREATE INDEX idx_journey_stage_orchestration ON project_journey_stages(orchestration_id);
CREATE INDEX idx_journey_stage_name ON project_journey_stages(stage_name);
CREATE INDEX idx_journey_stage_order ON project_journey_stages(stage_order);
CREATE INDEX idx_journey_stage_status ON project_journey_stages(status);

-- Touchpoints indexes
CREATE INDEX idx_touchpoint_orchestration ON project_touchpoints(orchestration_id);
CREATE INDEX idx_touchpoint_type ON project_touchpoints(touchpoint_type);
CREATE INDEX idx_touchpoint_date ON project_touchpoints(interaction_date);
CREATE INDEX idx_touchpoint_initiator ON project_touchpoints(initiated_by);
CREATE INDEX idx_touchpoint_stage ON project_touchpoints(related_stage);

-- Conversations indexes
CREATE INDEX idx_conversation_orchestration ON project_conversations(orchestration_id);
CREATE INDEX idx_conversation_id ON project_conversations(conversation_id);
CREATE INDEX idx_conversation_status ON project_conversations(status);
CREATE INDEX idx_conversation_start ON project_conversations(start_time);

-- Collaboration metrics indexes
CREATE INDEX idx_collaboration_orchestration ON agent_collaboration_metrics(orchestration_id);
CREATE INDEX idx_collaboration_agents ON agent_collaboration_metrics(primary_agent, secondary_agent);
CREATE INDEX idx_collaboration_period ON agent_collaboration_metrics(measurement_start, measurement_end);

-- =====================================================
-- Triggers for automatic updates
-- =====================================================

-- Update updated_at timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables
CREATE TRIGGER update_project_orchestrations_updated_at 
    BEFORE UPDATE ON project_orchestrations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_agent_assignments_updated_at 
    BEFORE UPDATE ON project_agent_assignments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_journey_stages_updated_at 
    BEFORE UPDATE ON project_journey_stages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_touchpoints_updated_at 
    BEFORE UPDATE ON project_touchpoints 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_conversations_updated_at 
    BEFORE UPDATE ON project_conversations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_collaboration_metrics_updated_at 
    BEFORE UPDATE ON agent_collaboration_metrics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Views for common queries
-- =====================================================

-- Active orchestrations view
CREATE VIEW active_orchestrations AS
SELECT 
    po.*,
    p.name as project_name,
    p.status as project_status,
    COUNT(paa.id) as assigned_agents_count,
    COUNT(CASE WHEN pjs.status = 'completed' THEN 1 END) as completed_stages_count,
    COUNT(pjs.id) as total_stages_count
FROM project_orchestrations po
JOIN projects p ON po.project_id = p.id
LEFT JOIN project_agent_assignments paa ON po.id = paa.orchestration_id AND paa.active = true
LEFT JOIN project_journey_stages pjs ON po.id = pjs.orchestration_id
WHERE po.orchestration_status = 'active'
GROUP BY po.id, p.name, p.status;

-- Journey progress view
CREATE VIEW journey_progress AS
SELECT 
    po.id as orchestration_id,
    po.current_stage,
    pjs.stage_name,
    pjs.stage_order,
    pjs.status,
    pjs.progress_percentage,
    pjs.start_date,
    pjs.end_date,
    pjs.satisfaction_score,
    pjs.efficiency_score
FROM project_orchestrations po
JOIN project_journey_stages pjs ON po.id = pjs.orchestration_id
ORDER BY po.id, pjs.stage_order;

-- Agent performance view
CREATE VIEW agent_performance AS
SELECT 
    paa.orchestration_id,
    paa.agent_name,
    paa.agent_role,
    paa.tasks_completed,
    paa.efficiency_score,
    paa.collaboration_score,
    paa.quality_score,
    paa.cost_incurred,
    paa.last_active,
    COUNT(pt.id) as touchpoints_initiated
FROM project_agent_assignments paa
LEFT JOIN project_touchpoints pt ON paa.agent_name = pt.initiated_by 
    AND paa.orchestration_id = pt.orchestration_id
WHERE paa.active = true
GROUP BY paa.id, paa.orchestration_id, paa.agent_name, paa.agent_role, 
         paa.tasks_completed, paa.efficiency_score, paa.collaboration_score, 
         paa.quality_score, paa.cost_incurred, paa.last_active;

-- =====================================================
-- Sample data for testing (optional)
-- =====================================================

-- Insert sample orchestration data (uncomment if needed for testing)
/*
INSERT INTO project_orchestrations (
    project_id, 
    primary_agent, 
    coordination_pattern,
    orchestration_status,
    current_stage
) VALUES (
    (SELECT id FROM projects LIMIT 1), -- Use existing project
    'ali-chief-of-staff',
    'hierarchical',
    'active',
    'planning'
) ON CONFLICT (project_id) DO NOTHING;
*/

-- =====================================================
-- Migration completion
-- =====================================================

-- Add comment to track migration
COMMENT ON TABLE project_orchestrations IS 'AI orchestration configuration and state for projects';
COMMENT ON TABLE project_agent_assignments IS 'Agent assignments and performance tracking for orchestrated projects';
COMMENT ON TABLE project_journey_stages IS 'CRM-style journey stages with progress tracking';
COMMENT ON TABLE project_touchpoints IS 'Interaction touchpoints for project engagement tracking';
COMMENT ON TABLE project_conversations IS 'Agent conversation tracking within projects';
COMMENT ON TABLE agent_collaboration_metrics IS 'Metrics for agent collaboration analysis';

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'PM Orchestration tables created successfully at %', NOW();
END
$$;