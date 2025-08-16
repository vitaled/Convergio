"""
Template Library API - Endpoints for managing custom field templates
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from src.services.template_library import (
    template_library,
    TemplateDefinition,
    FieldDefinition
)

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])


# ===================== Request/Response Models =====================

class FieldDefinitionRequest(BaseModel):
    name: str
    type: str
    label: str
    required: bool = False
    default_value: Any = None
    options: Optional[List[str]] = None
    validation: Optional[Dict[str, Any]] = None
    help_text: Optional[str] = None
    display_order: int = 0


class TemplateCreateRequest(BaseModel):
    id: str
    name: str
    domain: str
    description: str
    project_fields: List[FieldDefinitionRequest] = []
    task_fields: List[FieldDefinitionRequest] = []
    resource_fields: List[FieldDefinitionRequest] = []
    epic_fields: List[FieldDefinitionRequest] = []
    tags: List[str] = []
    icon: str = "template"
    color: str = "#6B7280"


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_fields: Optional[List[FieldDefinitionRequest]] = None
    task_fields: Optional[List[FieldDefinitionRequest]] = None
    resource_fields: Optional[List[FieldDefinitionRequest]] = None
    epic_fields: Optional[List[FieldDefinitionRequest]] = None
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class ApplyTemplateRequest(BaseModel):
    template_id: str
    entity_type: str  # project, task, resource, epic
    entity_id: str
    field_values: Dict[str, Any]


# ===================== Template CRUD Endpoints =====================

@router.get("/", response_model=List[TemplateDefinition])
async def list_templates(
    domain: Optional[str] = Query(None, description="Filter by domain (IT, Marketing, Legal, Finance, HR, Custom)")
):
    """List all available templates"""
    return template_library.list_templates(domain)


@router.get("/{template_id}", response_model=TemplateDefinition)
async def get_template(template_id: str):
    """Get a specific template by ID"""
    template = template_library.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    return template


@router.post("/", response_model=TemplateDefinition)
async def create_template(request: TemplateCreateRequest):
    """Create a new custom template"""
    try:
        # Convert request to TemplateDefinition
        template_data = request.dict()
        
        # Convert field definitions
        for field_type in ["project_fields", "task_fields", "resource_fields", "epic_fields"]:
            template_data[field_type] = [
                FieldDefinition(**field_dict) 
                for field_dict in template_data.get(field_type, [])
            ]
        
        template = TemplateDefinition(**template_data)
        return template_library.create_template(template)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{template_id}", response_model=TemplateDefinition)
async def update_template(template_id: str, request: TemplateUpdateRequest):
    """Update an existing template"""
    try:
        updates = request.dict(exclude_unset=True)
        
        # Convert field definitions if present
        for field_type in ["project_fields", "task_fields", "resource_fields", "epic_fields"]:
            if field_type in updates and updates[field_type] is not None:
                updates[field_type] = [
                    FieldDefinition(**field_dict) 
                    for field_dict in updates[field_type]
                ]
        
        return template_library.update_template(template_id, updates)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{template_id}/clone")
async def clone_template(
    template_id: str,
    new_id: str = Query(..., description="ID for the cloned template"),
    new_name: str = Query(..., description="Name for the cloned template")
):
    """Clone an existing template"""
    try:
        return template_library.clone_template(template_id, new_id, new_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """Delete a custom template"""
    try:
        success = template_library.delete_template(template_id)
        if success:
            return {"message": f"Template {template_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== Template Application Endpoints =====================

@router.get("/{template_id}/fields/{entity_type}")
async def get_template_fields(
    template_id: str,
    entity_type: str = Query(..., enum=["project", "task", "resource", "epic"])
):
    """Get fields for a specific entity type from a template"""
    try:
        fields = template_library.apply_template(template_id, entity_type)
        return {
            "template_id": template_id,
            "entity_type": entity_type,
            "fields": fields
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{template_id}/schema/{entity_type}")
async def get_template_schema(
    template_id: str,
    entity_type: str = Query(..., enum=["project", "task", "resource", "epic"])
):
    """Get JSON schema for custom fields validation"""
    try:
        schema = template_library.get_field_schema(template_id, entity_type)
        return {
            "template_id": template_id,
            "entity_type": entity_type,
            "schema": schema
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/apply")
async def apply_template_to_entity(request: ApplyTemplateRequest):
    """Apply a template to an entity and validate field values"""
    try:
        # Get template fields
        fields = template_library.apply_template(request.template_id, request.entity_type)
        
        # Validate each field value
        validation_errors = []
        validated_values = {}
        
        for field in fields:
            value = request.field_values.get(field.name)
            
            # Use default value if not provided
            if value is None and field.default_value is not None:
                value = field.default_value
            
            # Validate
            if not template_library.validate_field_value(field, value):
                validation_errors.append({
                    "field": field.name,
                    "message": f"Invalid value for field {field.label}"
                })
            else:
                validated_values[field.name] = value
        
        if validation_errors:
            return {
                "success": False,
                "errors": validation_errors
            }
        
        # In a real implementation, this would save to the database
        return {
            "success": True,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "template_id": request.template_id,
            "field_values": validated_values
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== Import/Export Endpoints =====================

@router.get("/{template_id}/export")
async def export_template(template_id: str):
    """Export a template as JSON"""
    try:
        json_data = template_library.export_template(template_id)
        return {
            "template_id": template_id,
            "data": json_data
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/import")
async def import_template(template_json: str):
    """Import a template from JSON"""
    try:
        template = template_library.import_template(template_json)
        return {
            "message": "Template imported successfully",
            "template_id": template.id,
            "template_name": template.name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import template: {str(e)}")


# ===================== Domain-Specific Endpoints =====================

@router.get("/domains/list")
async def list_domains():
    """List all available template domains"""
    domains = ["IT", "Marketing", "Legal", "Finance", "HR", "Custom"]
    
    # Count templates per domain
    domain_counts = {}
    for domain in domains:
        templates = template_library.list_templates(domain)
        domain_counts[domain] = len(templates)
    
    return {
        "domains": [
            {
                "name": domain,
                "template_count": domain_counts[domain],
                "icon": _get_domain_icon(domain),
                "color": _get_domain_color(domain)
            }
            for domain in domains
        ]
    }


def _get_domain_icon(domain: str) -> str:
    """Get icon for domain"""
    icons = {
        "IT": "code",
        "Marketing": "megaphone",
        "Legal": "scale",
        "Finance": "currency-dollar",
        "HR": "users",
        "Custom": "puzzle"
    }
    return icons.get(domain, "template")


def _get_domain_color(domain: str) -> str:
    """Get color for domain"""
    colors = {
        "IT": "#3B82F6",
        "Marketing": "#8B5CF6",
        "Legal": "#EF4444",
        "Finance": "#10B981",
        "HR": "#F59E0B",
        "Custom": "#6B7280"
    }
    return colors.get(domain, "#6B7280")


# ===================== Quick Start Templates =====================

@router.post("/quick-start/{domain}")
async def create_quick_start_project(
    domain: str = Query(..., enum=["IT", "Marketing", "Legal", "Finance", "HR"]),
    project_name: str = Query(..., description="Name for the new project")
):
    """Create a new project with a pre-configured template"""
    # Map domains to default templates
    template_map = {
        "IT": "it_project",
        "Marketing": "marketing_campaign",
        "Legal": "legal_contract",
        "Finance": "finance_budget",
        "HR": "hr_recruitment"
    }
    
    template_id = template_map.get(domain)
    if not template_id:
        raise HTTPException(status_code=400, detail=f"No default template for domain {domain}")
    
    template = template_library.get_template(template_id)
    
    # In a real implementation, this would create the project with the template
    return {
        "message": f"Project created with {domain} template",
        "project_name": project_name,
        "template_used": template.name,
        "custom_fields": {
            "project": len(template.project_fields),
            "task": len(template.task_fields),
            "resource": len(template.resource_fields),
            "epic": len(template.epic_fields)
        }
    }