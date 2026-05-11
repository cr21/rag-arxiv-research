from fastapi import APIRouter
from sqlalchemy import text

from ..dependencies import DatabaseDep, SettingsDep, OpenSearchDep, OllamaDep
from ..schemas.api.health import HealthResponse, ServiceStatus

router = APIRouter()


@router.get("/ping",tags=["Health"])
async def ping():
    """
    simple ping command to test the connectivity test
    """
    return  {'status':'ok', 'message':'pong'}


@router.get("/health",
tags=["Health"],
response_model=HealthResponse,
summary="Health check endpoint",
description="Check the health and status of the API service including database connectivity.",
response_description="Service health information",
)
async def health_check(
    settings: SettingsDep,
    database: DatabaseDep,
    opensearch_client: OpenSearchDep,
    ollama_client: OllamaDep,
):
    """
    Comprehensive health check endpoint for monitoring and load balancer probes.

    This endpoint provides information about the service health, version,
    environment, and checks connectivity to dependent services like database.

    Returns:
        HealthResponse: Contains service status, version, environment, and service checks

    Example:
    ```json
    {
        "status": "ok",
        "version": "0.1.0",
        "environment": "development",
        "service_name": "rag-api",
        "services": {"ollama": {"status": "ok", "message": "Service is running"},
         "opensearch": {"status": "ok", "message": "Service is running"},
          "pdf_parser": {"status": "ok", "message": "Service is running"}, 
          "database": {"status": "ok", "message": "Service is running"}}
    }
    ```
    """
    services = {

    }
    overall_status='ok'

    def _check_service(name: str, check_func, *args, **kwargs):
        """Helper to standardize service health checks."""
        try:
            if kwargs.get("is_async"):
                # Handle async functions separately in the calling code
                return check_func(*args)
            result = check_func(*args)
            services[name] = result
            if result.status not in ("healthy", "ok"):
                nonlocal overall_status
                overall_status = "degraded"
        except Exception as e:
            services[name] = ServiceStatus(status="unhealthy", message=str(e))
            overall_status = "degraded"
    # Test database connectivity
    def _check_database():
        with database.get_session() as session:
            session.execute(text("SELECT 1"))
        return  ServiceStatus(status="healthy", message="Database connectivity successful")
    
    def _check_opensearch():
        if not opensearch_client.health_check():
            return ServiceStatus(status="unhealthy", message="OpenSearch connectivity failed")
        stats = opensearch_client.get_index_stats()
        return ServiceStatus(status="healthy",
                        message=f"Index '{stats.get('index_name', 'unknown')}' with {stats.get('document_count', 0)} documents"
                        )
    # Run health check synchoronoulsy
    _check_service("database", _check_database)
    _check_service("opensearch", _check_opensearch)

    #Test ollama connectivity
    try:
        ollama_health = await ollama_client.health_check()
        if ollama_health.get("status") in ("healthy", "ok"):
            services["ollama"] = ServiceStatus(status="healthy", message=ollama_health.get("message", "Ollama ok"))
        else:
            overall_status = "degraded"
            services["ollama"] = ServiceStatus(
                status="unhealthy",
                message=f"Ollama connectivity failed: {ollama_health.get('message', 'unknown error')}",
            )
    except Exception as e:
        overall_status = "degraded"
        services["ollama"] = ServiceStatus(status="unhealthy", message=f"Ollama connectivity failed: {e}")
    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        service_name=settings.service_name,
        services=services
    )