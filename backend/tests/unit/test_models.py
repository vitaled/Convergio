#!/usr/bin/env python3
"""
Unit tests for database models
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock

from src.models.document import Document, DocumentEmbedding
from src.models.talent import Talent
from src.models.user import User


class TestDocumentModel:
    """Test Document model functionality"""
    
    def test_document_creation(self):
        """Test basic document creation"""
        doc = Document(
            title="Test Document",
            content="This is test content",
            doc_metadata={"type": "test", "category": "unit-test"}
        )
        
        assert doc.title == "Test Document"
        assert doc.content == "This is test content"
        assert doc.doc_metadata["type"] == "test"
    
    def test_document_defaults(self):
        """Test document default values"""
        doc = Document(
            title="Minimal Document",
            content="Content"
        )
        
        assert doc.is_active is True
        assert doc.doc_metadata is None
        assert doc.tags is None
    
    def test_document_string_representation(self):
        """Test document string representation"""
        doc = Document(
            title="String Test",
            content="Content"
        )
        doc.id = 1
        
        str_repr = str(doc)
        assert "String Test" in str_repr or "1" in str_repr


class TestDocumentEmbedding:
    """Test DocumentEmbedding model"""
    
    def test_embedding_creation(self):
        """Test embedding creation with vector"""
        embedding = DocumentEmbedding(
            document_id=1,
            embedding_vector=[0.1, 0.2, 0.3, 0.4],
            embedding_metadata={"model": "text-embedding-ada-002"}
        )
        
        assert embedding.document_id == 1
        assert len(embedding.embedding_vector) == 4
        assert embedding.embedding_metadata["model"] == "text-embedding-ada-002"
    
    def test_embedding_defaults(self):
        """Test embedding default values"""
        embedding = DocumentEmbedding(
            document_id=1,
            embedding_vector=[0.1, 0.2]
        )
        
        assert embedding.embedding_metadata is None
        assert embedding.created_at is not None


class TestTalentModel:
    """Test Talent model functionality"""
    
    def test_talent_creation(self):
        """Test basic talent creation"""
        talent = Talent(
            name="John Developer",
            email="john@example.com",
            skills=["Python", "FastAPI", "PostgreSQL"],
            experience_level="senior",
            bio="Senior full-stack developer"
        )
        
        assert talent.name == "John Developer"
        assert talent.email == "john@example.com"
        assert "Python" in talent.skills
        assert talent.experience_level == "senior"
    
    def test_talent_defaults(self):
        """Test talent default values"""
        talent = Talent(
            name="Minimal Talent",
            email="minimal@example.com"
        )
        
        assert talent.is_active is True
        assert talent.skills == []
        assert talent.bio is None
    
    def test_talent_validation(self):
        """Test talent field validation"""
        # Test valid experience levels
        valid_levels = ["junior", "mid", "senior", "lead", "principal"]
        
        for level in valid_levels:
            talent = Talent(
                name=f"Test {level}",
                email=f"{level}@example.com",
                experience_level=level
            )
            assert talent.experience_level == level


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self):
        """Test basic user creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
    
    def test_user_defaults(self):
        """Test user default values"""
        user = User(
            username="defaultuser",
            email="default@example.com"
        )
        
        assert user.is_active is True
        assert user.full_name is None
        assert user.created_at is not None
    
    def test_user_string_representation(self):
        """Test user string representation"""
        user = User(
            username="repruser",
            email="repr@example.com"
        )
        user.id = 123
        
        str_repr = str(user)
        assert "repruser" in str_repr or "123" in str_repr


class TestModelRelationships:
    """Test model relationships and associations"""
    
    def test_document_embedding_relationship(self):
        """Test document to embedding relationship"""
        doc = Document(
            title="Related Document",
            content="This document has embeddings"
        )
        doc.id = 1
        
        embedding = DocumentEmbedding(
            document_id=doc.id,
            embedding_vector=[0.1, 0.2, 0.3]
        )
        
        assert embedding.document_id == doc.id
    
    def test_talent_user_association(self):
        """Test talent and user can be associated"""
        user = User(
            username="talentuser",
            email="talent@example.com"
        )
        user.id = 1
        
        talent = Talent(
            name="User's Talent Profile",
            email="talent@example.com"
        )
        
        # In a real scenario, these might be linked by user_id
        assert user.email == talent.email


class TestModelMethods:
    """Test model instance methods"""
    
    def test_document_content_length(self):
        """Test document content analysis"""
        short_doc = Document(
            title="Short",
            content="Brief content"
        )
        
        long_doc = Document(
            title="Long",
            content="A" * 1000
        )
        
        assert len(short_doc.content) < 50
        assert len(long_doc.content) >= 1000
    
    def test_talent_skill_management(self):
        """Test talent skill operations"""
        talent = Talent(
            name="Skill Manager",
            email="skills@example.com",
            skills=["Python", "JavaScript"]
        )
        
        # Add skill
        talent.skills.append("TypeScript")
        assert "TypeScript" in talent.skills
        
        # Remove skill
        if "JavaScript" in talent.skills:
            talent.skills.remove("JavaScript")
        assert "JavaScript" not in talent.skills
    
    def test_user_active_status(self):
        """Test user active status management"""
        user = User(
            username="statususer",
            email="status@example.com"
        )
        
        # Default active
        assert user.is_active is True
        
        # Deactivate
        user.is_active = False
        assert user.is_active is False
        
        # Reactivate
        user.is_active = True
        assert user.is_active is True