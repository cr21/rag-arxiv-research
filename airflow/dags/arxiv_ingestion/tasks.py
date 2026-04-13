import asyncio
import logging
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Tuple

# DAG parsing runs before task execution; ensure parent of `src` is on path.
_airflow_root = "/opt/airflow"
if _airflow_root not in sys.path:
    sys.path.insert(0, _airflow_root)

from src.repositories.paper import PaperRepository

# All imports at the top
from sqlalchemy import text
from src.db.factory import make_database
from src.services.arxiv.factory import make_arxiv_client
from src.services.metadata_fetcher import make_metadata_fetcher
from src.services.pdf_parser.factory import make_pdf_parser_service
from src.services.opensearch.factory import make_opensearch_client

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_cached_services() -> Tuple[Any, Any, Any, Any, Any]:
    """
    Get cached service instances using lru_cache for automatic memoization.

    Returns:
        Tuple of (arxiv_client, pdf_parser, database, metadata_fetcher, opensearch_client)
    """
    logger.info("Initializing services (cached with lru_cache)")

    # Initialize core services
    arxiv_client = make_arxiv_client()
    pdf_parser = make_pdf_parser_service()
    database = make_database()
    opensearch_client = make_opensearch_client()
    # Create metadata fetcher with dependencies
    metadata_fetcher = make_metadata_fetcher(arxiv_client, pdf_parser)

    logger.info("All services initialized and cached with lru_cache")
    return arxiv_client, pdf_parser, database, metadata_fetcher, opensearch_client



async def run_paper_ingestion_pipeline(
    target_date: str,
    max_results: int = 5,
    process_pdfs: bool = True,
) -> dict:
    """
    Async wrapper for the paper ingestion pipeline.

    Args:
        target_date: Date to fetch papers for (YYYYMMDD format)
        max_results: Maximum number of papers to fetch
        process_pdfs: Whether to process PDFs

    Returns:
        Dictionary with processing results
    """
    _arxiv_client, _pdf_parser, database, metadata_fetcher, _opensearch = get_cached_services()

    with database.get_session() as session:
        return await metadata_fetcher.fetch_and_process_papers(
            max_results=max_results,
            from_date=target_date,
            to_date=target_date,
            process_pdfs=process_pdfs,
            store_to_db=True,
            db_session=session,
        )


def setup_environment():
    """Setup environment and verify dependencies."""
    logger.info("Setting up environment for arXiv paper ingestion")

    try:
        # Get cached services (initialized once)
        arxiv_client, _pdf_parser, database, _metadata_fetcher, opensearch_client = get_cached_services()

        # Test database connection
        with database.get_session() as session:
            session.execute(text("SELECT 1"))
            logger.info("Database connection verified")
        
        # Test OpenSearch connection and create index if needed
        if opensearch_client.health_check():
            logger.info("OpenSearch connection verified")
            # Ensure index exists
            if opensearch_client.create_index(force=False):
                logger.info("OpenSearch index created")
            else:
                logger.info("OpenSearch index already exists")
        else:
            logger.warning("OpenSearch not healthy, indexing will be skipped")
        logger.info(f"arXiv client ready: {arxiv_client.base_url}")
        logger.info("PDF parser service ready (Docling models cached)")

        return {"status": "success", "message": "Environment setup completed"}

    except Exception as e:
        error_msg = f"Environment setup failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def fetch_daily_papers(**context):
    """
    Fetch CS.AI papers from the last 24 hours.

    This function:
    1. Calculates the date range for yesterday
    2. Fetches papers using the MetadataFetcher
    3. Returns processing statistics
    """
    logger.info("Starting daily arXiv paper fetch")

    try:
        # Calculate date range (yesterday - execution_date - 1)
        execution_date = context["ds"]  # YYYY-MM-DD format
        execution_dt = datetime.strptime(execution_date, "%Y-%m-%d")
        target_dt = execution_dt - timedelta(days=1)  # Get papers from day before
        target_date = target_dt.strftime("%Y%m%d")

        logger.info(f"Fetching papers for date: {target_date}")

        # Execute paper ingestion pipeline
        results = asyncio.run(
            run_paper_ingestion_pipeline(
                target_date=target_date,
                max_results=20,
                process_pdfs=True,
            )
        )
        logger.info(f"Daily paper fetch completed: {results}")

        # Store results for downstream tasks
        context["task_instance"].xcom_push(key="fetch_results", value=results)

        return results

    except Exception as e:
        error_msg = f"Daily paper fetch failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def index_papers_to_opensearch(**context):
    """Index stored papers from PostgreSQL to OpenSearch.

    This is the single dedicated task for OpenSearch indexing to avoid duplication.
    It reads papers stored by fetch_daily_papers and indexes them to OpenSearch.
    """
    logger.info("Starting OpenSearch indexing Task")
    try:
        fetch_results = context["task_instance"].xcom_pull(task_ids="fetch_daily_papers", key="fetch_results")

        if not fetch_results:
            logger.warning("No fetch results available for OpenSearch indexing")
            return {"status": "skipped", "message": "No papers to process"}
        papers_stored = fetch_results.get("papers_stored", 0)

        if papers_stored == 0:
            logger.info("No papers were stored, skipping OpenSearch indexing")
            return {"status": "skipped", "papers_indexed": 0, "message": "No papers available for indexing"}
        logger.info(f"Processing {papers_stored} papers for OpenSearch indexing")
        # Get all services 
        _arxiv_client, _pdf_parser, database, _metadata_fetcher, opensearch_client = get_cached_services()
        # check opensearch health
        if not opensearch_client.health_check():
            logger.error("OpenSearch is not healthy, skipping indexing")
            return {"status": "failed", "papers_indexed": 0, "message": "OpenSearch cluster not healthy"}
        fetch_results = context["task_instance"].xcom_pull(task_ids="fetch_daily_papers", key="fetch_results")
        indexed_count = 0
        failed_count = 0

        with database.get_session() as session:
            paper_repo = PaperRepository(session)
            limit_n = int(fetch_results.get("papers_stored", 0) or 0)
            query = f"""
            SELECT * FROM papers
            WHERE created_at::date = CURRENT_DATE
            ORDER BY created_at DESC
            LIMIT {fetch_results.get("papers_stored", 0) if fetch_results else 100}
            """
            logger.info(f"Query: {query}")
            result = session.execute(text(query))
            papers = result.fetchall()
            logger.info(f"Found {len(papers)} papers to index")

            for paper_row in papers:
                try:
                    paper = paper_repo.get_by_id(paper_row.id)
                    if not paper:
                        continue
                    paper_doc = {
                        "arxiv_id": paper.arxiv_id,
                        "title": paper.title,
                        "authors": ", ".join(paper.authors) if isinstance(paper.authors, list) else str(paper.authors),
                        "abstract": paper.abstract,
                        "categories": paper.categories,
                        "pdf_url": paper.pdf_url,
                        "published_date": paper.published_date.isoformat()
                        if hasattr(paper.published_date, "isoformat")
                        else str(paper.published_date),
                        "raw_text": paper.raw_text
                        if hasattr(paper, "raw_text") and paper.raw_text
                        else "",  # Include PDF content
                        "created_at": paper.created_at.isoformat()
                        if hasattr(paper.created_at, "isoformat")
                        else str(paper.created_at),
                        "updated_at": paper.updated_at.isoformat()
                        if hasattr(paper.updated_at, "isoformat")
                        else str(paper.updated_at),
                    }
                    success = opensearch_client.index_paper(paper_doc)
                    if success:
                        indexed_count += 1
                        logger.info(f"Successfully indexed paper: {paper.arxiv_id}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to index paper: {paper.arxiv_id}")
                except Exception as e:
                    logger.error(f"Error indexing paper {paper_row.arxiv_id}: {e}")
                    failed_count += 1
            
            # GEt the final stats
        try:
            final_stats = opensearch_client.get_index_stats()
            total_docs = final_stats.get("document_count", 0) if final_stats else 0
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            total_docs = "unknown"
        
        indexing_results = {
            "status": "completed",
            "papers_indexed": indexed_count,
            "indexing_failures": failed_count,
            "total_documents_in_index": total_docs,
            "message": f"Indexed {indexed_count} papers, {failed_count} failures",
        }
        # Log detailed summary
        logger.info("=" * 60)
        logger.info("OpenSearch Indexing Summary:")
        logger.info(f"  Papers found in DB: {len(papers)}")
        logger.info(f"  Papers indexed: {indexed_count}")
        logger.info(f"  Indexing failures: {failed_count}")
        logger.info(f"  Total docs in index: {total_docs}")
        logger.info("=" * 60)

        return indexing_results


    except Exception as e:
        error_msg = f"OpenSearch indexing failed: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "papers_indexed": 0, "message": error_msg}

def process_failed_pdfs(**context):
    """
    Retry processing of PDFs that failed in the main fetch task.

    This function:
    1. Gets failed PDF list from the main task
    2. Retries processing with different settings
    3. Reports final success/failure statistics
    """
    logger.info("Processing failed PDFs")

    try:
        fetch_results = context["task_instance"].xcom_pull(task_ids="fetch_daily_papers", key="fetch_results")

        if not fetch_results or not fetch_results.get("errors"):
            logger.info("No failed PDFs to retry")
            return {"status": "skipped", "message": "No failures to retry"}

        logger.info(f"Found {len(fetch_results['errors'])} errors to investigate")

        for error in fetch_results["errors"]:
            # TODO: Implement retry logic
            logger.warning(f"Error to investigate: {error}")

        return {
            "status": "analyzed",
            "errors_logged": len(fetch_results["errors"]),
            "message": "Errors logged for investigation",
        }

    except Exception as e:
        error_msg = f"Failed PDF processing error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)



def create_opensearch_placeholders(**context):
    """
    Create placeholder entries for OpenSearch indexing.

    This is a Week 2 placeholder - in Week 3+ this will:
    1. Get successfully stored papers
    2. Create placeholder OpenSearch documents
    3. Prepare for actual indexing pipeline
    """
    logger.info("Creating OpenSearch placeholders (Week 2)")

    try:
        fetch_results = context["task_instance"].xcom_pull(task_ids="fetch_daily_papers", key="fetch_results")

        if not fetch_results:
            logger.warning("No fetch results available for OpenSearch placeholders")
            return {"status": "skipped", "message": "No papers to process"}

        papers_stored = fetch_results.get("papers_stored", 0)

        logger.info(f"Creating placeholders for {papers_stored} papers")

        # Week 2: Just log what would be indexed
        # Week 3+: Actually create OpenSearch documents
        placeholder_results = {
            "status": "placeholder",
            "papers_ready_for_indexing": papers_stored,
            "message": f"Week 2: {papers_stored} papers ready for future OpenSearch indexing",
        }

        logger.info(f"OpenSearch placeholders: {placeholder_results}")

        return placeholder_results

    except Exception as e:
        error_msg = f"OpenSearch placeholder creation failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def generate_daily_report(**context):
    """
    Generate a daily processing report.

    This function:
    1. Collects results from all tasks
    2. Generates summary statistics
    3. Logs the daily report
    """
    logger.info("Generating daily processing report")

    try:
        fetch_results = context["task_instance"].xcom_pull(task_ids="fetch_daily_papers", key="fetch_results")

        opensearch_results = context["task_instance"].xcom_pull(task_ids="index_papers_to_opensearch")

        
        report = {
            "date": context["ds"],
            "execution_time": datetime.now().isoformat(),
            "papers": {
                "fetched": fetch_results.get("papers_fetched", 0) if fetch_results else 0,
                "pdfs_downloaded": fetch_results.get("pdfs_downloaded", 0) if fetch_results else 0,
                "pdfs_parsed": fetch_results.get("pdfs_parsed", 0) if fetch_results else 0,
                "stored": fetch_results.get("papers_stored", 0) if fetch_results else 0,
            },
            "processing": {
                "processing_time_seconds": fetch_results.get("processing_time", 0) if fetch_results else 0,
                "errors": len(fetch_results.get("errors", [])) if fetch_results else 0,
                "failed_pdf_retries": len(fetch_results.get("errors", [])) if fetch_results else 0,
                "pdf_failures_skipped": fetch_results.get("pdf_failures_skipped", 0) if fetch_results else 0,
            },
            "opensearch": {
                "papers_indexed": opensearch_results.get("papers_indexed", 0) if opensearch_results else 0,
                "indexing_failures": opensearch_results.get("indexing_failures", 0) if opensearch_results else 0,
                "total_documents_in_index": opensearch_results.get("total_documents_in_index", 0) if opensearch_results else 0,
                "status": opensearch_results.get("status", "unknown") if opensearch_results else "unknown",
            },
        }

        logger.info("=== DAILY ARXIV PROCESSING REPORT ===")
        logger.info(f"Date: {report['date']}")
        logger.info(f"Papers fetched: {report['papers']['fetched']}")
        logger.info(f"PDFs downloaded: {report['papers']['pdfs_downloaded']}")
        logger.info(f"PDFs parsed: {report['papers']['pdfs_parsed']}")
        logger.info(f"Papers stored: {report['papers']['stored']}")
        logger.info(f"Processing time: {report['processing']['processing_time_seconds']:.1f}s")
        logger.info(f"PDF failures (oversized docs skipped): {report['processing']['pdf_failures_skipped']}")
        logger.info(f"OpenSearch indexed: {report['opensearch']['papers_indexed']}")
        logger.info(f"OpenSearch failures: {report['opensearch']['indexing_failures']}")
        logger.info(f"Total in index: {report['opensearch']['total_documents_in_index']}")
        logger.info(f"OpenSearch status: {report['opensearch']['status']}")
        logger.info("=== END REPORT ===")

        return report

    except Exception as e:
        error_msg = f"Report generation failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
