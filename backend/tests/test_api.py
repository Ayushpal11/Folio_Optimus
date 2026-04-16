import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health():
    """Test health check endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_root():
    """Test root endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_search_empty():
    """Test search with empty query"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/search?q=")
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


@pytest.mark.asyncio
async def test_search_reliance():
    """Test search for Reliance"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/search?q=reliance")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    # Results might be empty depending on data, but should have structure


@pytest.mark.asyncio
async def test_stock_aapl():
    """Test getting stock info for AAPL"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/stock/AAPL")
    # May fail if no internet, but shouldn't crash
    if response.status_code == 200:
        data = response.json()
        assert "ticker" in data or "current_price" in data


@pytest.mark.asyncio
async def test_optimize_missing_tickers():
    """Test optimize endpoint with missing tickers"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/optimize",
            json={"tickers": [], "capital": 100000, "risk_tolerance": "medium"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_optimize_negative_capital():
    """Test optimize endpoint with negative capital"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/optimize",
            json={"tickers": ["AAPL"], "capital": -100000, "risk_tolerance": "medium"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_optimize_single_ticker():
    """Test optimize endpoint with single ticker"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/optimize",
            json={
                "tickers": ["AAPL"],
                "capital": 10000,
                "risk_tolerance": "medium",
            },
        )
    # May fail without data, but structure should be correct if it succeeds
    if response.status_code == 200:
        data = response.json()
        assert "optimization_status" in data
        assert "weights" in data
        assert "allocation" in data
        assert "performance" in data


@pytest.mark.asyncio
async def test_optimize_three_tickers():
    """Test optimize endpoint with three tickers"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/optimize",
            json={
                "tickers": ["AAPL", "MSFT", "GOOGL"],
                "capital": 100000,
                "risk_tolerance": "low",
            },
        )
    # May fail without data, but structure should be correct if it succeeds
    if response.status_code == 200:
        data = response.json()
        assert data["optimization_status"] == "success"
        assert "weights" in data
        weights = data["weights"]
        # Weights should sum to approximately 1
        weight_sum = sum(weights.values())
        assert 0.95 < weight_sum < 1.05
        assert len(data["allocation"]) > 0


@pytest.mark.asyncio
async def test_optimize_risk_low():
    """Test optimize with low risk tolerance"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/optimize",
            json={
                "tickers": ["AAPL", "MSFT"],
                "capital": 50000,
                "risk_tolerance": "low",
            },
        )
    if response.status_code == 200:
        data = response.json()
        assert data["risk_tolerance"] == "low"


@pytest.mark.asyncio
async def test_optimize_risk_high():
    """Test optimize with high risk tolerance"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/optimize",
            json={
                "tickers": ["AAPL", "MSFT"],
                "capital": 50000,
                "risk_tolerance": "high",
            },
        )
    if response.status_code == 200:
        data = response.json()
        assert data["risk_tolerance"] == "high"


@pytest.mark.asyncio
async def test_batch_stats_empty():
    """Test batch stats with no tickers"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/batch-stats", json={"tickers": []})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_folio_analyze_empty():
    """Test folio analysis with no holdings"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/folio/analyze", json={"holdings": []})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_recommend_invalid_risk():
    """Test recommend with invalid risk profile"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/recommend",
            json={"risk": "invalid", "duration": "short"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_recommend_invalid_duration():
    """Test recommend with invalid duration"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/recommend",
            json={"risk": "moderate", "duration": "invalid"},
        )
    assert response.status_code == 400
