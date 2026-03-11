"""
Tests for CoreOrchestrator
"""

import pytest
from core.orchestrator import CoreOrchestrator
from models.agent import UserRequest, IntentType


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initializes correctly"""
    assert orchestrator is not None
    assert orchestrator.memory is not None
    assert orchestrator.tools is not None
    assert orchestrator.event_bus is not None


@pytest.mark.asyncio
async def test_analyze_intent_feature(orchestrator):
    """Test intent analysis for feature request"""
    request = UserRequest(
        text="Add user authentication",
        user_id="test",
        session_id="test"
    )
    
    intent = await orchestrator._analyze_intent(request)
    
    assert intent.type == IntentType.SPEC
    assert intent.spec_type == "feature"
    assert "authentication" in intent.keywords or "user" in intent.keywords


@pytest.mark.asyncio
async def test_analyze_intent_bugfix(orchestrator):
    """Test intent analysis for bugfix request"""
    request = UserRequest(
        text="Fix crash when quantity is zero",
        user_id="test",
        session_id="test"
    )
    
    intent = await orchestrator._analyze_intent(request)
    
    assert intent.type == IntentType.SPEC
    assert intent.spec_type == "bugfix"


@pytest.mark.asyncio
async def test_determine_workflow_feature_requirements_first(orchestrator):
    """Test workflow determination for feature requirements-first"""
    from models.agent import IntentAnalysis, SpecType, WorkflowTypeEnum
    
    intent = IntentAnalysis(
        type=IntentType.SPEC,
        spec_type=SpecType.FEATURE,
        workflow_type=WorkflowTypeEnum.REQUIREMENTS_FIRST,
        keywords=["auth"]
    )
    
    workflow = await orchestrator._determine_workflow(intent)
    
    assert workflow == "feature-requirements-first-workflow"


@pytest.mark.asyncio
async def test_determine_workflow_bugfix(orchestrator):
    """Test workflow determination for bugfix"""
    from models.agent import IntentAnalysis, SpecType
    
    intent = IntentAnalysis(
        type=IntentType.SPEC,
        spec_type=SpecType.BUGFIX,
        keywords=["crash"]
    )
    
    workflow = await orchestrator._determine_workflow(intent)
    
    assert workflow == "bugfix-workflow"


@pytest.mark.asyncio
async def test_extract_feature_name(orchestrator):
    """Test feature name extraction"""
    name = orchestrator._extract_feature_name("Add user authentication with JWT")
    
    assert name == "add-user-authentication-with"
    assert "-" in name
    assert name.islower()


@pytest.mark.asyncio
async def test_detect_spec_type_feature(orchestrator):
    """Test spec type detection for feature"""
    spec_type = orchestrator._detect_spec_type("Add new dashboard feature")
    
    assert spec_type == "feature"


@pytest.mark.asyncio
async def test_detect_spec_type_bugfix(orchestrator):
    """Test spec type detection for bugfix"""
    spec_type = orchestrator._detect_spec_type("Fix bug in login form")
    
    assert spec_type == "bugfix"


@pytest.mark.asyncio
async def test_extract_keywords(orchestrator):
    """Test keyword extraction"""
    keywords = orchestrator._extract_keywords("Create user authentication system")
    
    assert "create" in keywords or "user" in keywords or "authentication" in keywords
    assert "the" not in keywords  # Stop words removed
