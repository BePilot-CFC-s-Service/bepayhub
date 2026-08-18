from supabase import create_client, Client
from config import Settings

class SupabaseRepository:
    _read_client: Client = None
    _write_client: Client = None

    @classmethod
    def _get_read_client(cls) -> Client:
        """Cliente apenas para leitura (anon key)"""
        if cls._read_client is None:
            cls._read_client = create_client(
                Settings.SUPABASE_URL,
                Settings.SUPABASE_KEY
            )
        return cls._read_client

    @classmethod
    def _get_write_client(cls) -> Client:
        """
        Cliente para escrita (service_role key).
        Se não houver service_role, usa a anon (pode falhar se RLS bloquear).
        """
        if cls._write_client is None:
            key = Settings.SUPABASE_SERVICE_ROLE_KEY or Settings.SUPABASE_KEY
            cls._write_client = create_client(
                Settings.SUPABASE_URL,
                key
            )
        return cls._write_client

    @classmethod
    def fetch_one(cls, table: str, query: dict) -> dict:
        """Busca um único registro com base em filtros de igualdade."""
        client = cls._get_read_client()
        builder = client.table(table).select("*")
        for key, value in query.items():
            builder = builder.eq(key, value)
        result = builder.execute()
        if result.data:
            return result.data[0]
        return None

    @classmethod
    def fetch_all(cls, table: str, query: dict = None) -> list:
        """
        Busca todos os registros que atendem aos filtros.
        Para filtro de diferença, use {'campo': {'neq': valor}}.
        """
        client = cls._get_read_client()
        builder = client.table(table).select("*")
        if query:
            for key, value in query.items():
                if isinstance(value, dict) and "neq" in value:
                    builder = builder.neq(key, value["neq"])
                else:
                    builder = builder.eq(key, value)
        result = builder.execute()
        return result.data

    @classmethod
    def insert(cls, table: str, data: dict) -> dict:
        client = cls._get_write_client()
        result = client.table(table).insert(data).execute()
        if result.data:
            return result.data[0]
        return None

    @classmethod
    def update(cls, table: str, query: dict, data: dict) -> dict:
        client = cls._get_write_client()
        builder = client.table(table).update(data)
        for key, value in query.items():
            builder = builder.eq(key, value)
        result = builder.execute()
        if result.data:
            return result.data[0]
        return None

    @classmethod
    def delete(cls, table: str, query: dict) -> bool:
        client = cls._get_write_client()
        builder = client.table(table).delete()
        for key, value in query.items():
            builder = builder.eq(key, value)
        result = builder.execute()
        return bool(result.data)