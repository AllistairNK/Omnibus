"""
Supabase client integration for authentication and storage.
"""
import logging
from typing import Optional, Dict, Any

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client wrapper for authentication and storage operations."""

    _instance: Optional["SupabaseClient"] = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize Supabase client."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_KEY environment variables."
            )
            return

        try:
            # Create Supabase client with custom options
            options = ClientOptions(
                auto_refresh_token=True,
                persist_session=True,
                detect_session_in_url=True,
            )
            self._client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY,
                options=options,
            )
            logger.info(f"Supabase client initialized for {settings.SUPABASE_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    @property
    def client(self) -> Client:
        """Get the Supabase client instance."""
        if self._client is None:
            raise RuntimeError("Supabase client not initialized. Check credentials.")
        return self._client

    # Authentication methods
    async def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user."""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
            })
            return response
        except Exception as e:
            logger.error(f"Sign up failed: {e}")
            raise

    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in an existing user."""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            return response
        except Exception as e:
            logger.error(f"Sign in failed: {e}")
            raise

    async def sign_out(self) -> None:
        """Sign out the current user."""
        try:
            self.client.auth.sign_out()
        except Exception as e:
            logger.error(f"Sign out failed: {e}")
            raise

    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user."""
        try:
            response = self.client.auth.get_user()
            return response.user if response else None
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return None

    # Storage methods
    async def upload_file(
        self,
        bucket: str,
        path: str,
        file_content: bytes,
        file_type: str = "text/plain",
    ) -> Dict[str, Any]:
        """Upload a file to Supabase Storage."""
        try:
            response = self.client.storage.from_(bucket).upload(
                path=path,
                file=file_content,
                file_options={"content-type": file_type},
            )
            return response
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise

    async def get_file_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file in Supabase Storage."""
        try:
            response = self.client.storage.from_(bucket).get_public_url(path)
            return response
        except Exception as e:
            logger.error(f"Failed to get file URL: {e}")
            raise

    async def delete_file(self, bucket: str, path: str) -> Dict[str, Any]:
        """Delete a file from Supabase Storage."""
        try:
            response = self.client.storage.from_(bucket).remove([path])
            return response
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            raise

    # Database methods (using Supabase PostgREST)
    async def from_table(self, table: str):
        """Get a query builder for a specific table."""
        return self.client.table(table)

    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a record into a table."""
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise

    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
    ) -> list:
        """Select records from a table."""
        try:
            query = self.client.table(table).select(columns)
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Select failed: {e}")
            raise

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
    ) -> list:
        """Update records in a table."""
        try:
            query = self.client.table(table).update(data)
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise

    async def delete(self, table: str, filters: Dict[str, Any]) -> list:
        """Delete records from a table."""
        try:
            query = self.client.table(table).delete()
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise


# Global Supabase client instance
supabase = SupabaseClient()


async def get_supabase() -> SupabaseClient:
    """Get Supabase client instance for dependency injection."""
    return supabase