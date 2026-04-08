from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schema.exceptions import DatabaseNotFoundError, SchemaFetchError
from app.schema.models import (
    SchemaResponse, SchemaTableResponse, SchemaColumnResponse, SchemaIndexResponse
)
from database.models.metadata import (
    Database, Table, ColumnModel, Index, IndexColumn
)


async def get_database_schema(db: AsyncSession, database_public_id: UUID) -> SchemaResponse:
    try:
        # 1. Fetch the database
        db_result = await db.execute(
            select(Database).where(Database.public_id == database_public_id, Database.deleted_at.is_(None))
        )
        database = db_result.scalar_one_or_none()

        if not database:
            raise DatabaseNotFoundError(str(database_public_id))

        # 2. Fetch all active tables
        tables_result = await db.execute(
            select(Table).where(Table.database_id == database.id, Table.deleted_at.is_(None))
        )
        tables = tables_result.scalars().all()
        table_ids = [t.id for t in tables]
        
        # Mapping table internal id to public id for foreign key resolution
        table_id_to_public = {t.id: t.public_id for t in tables}

        # 3. Fetch all active columns for these tables
        columns_result = await db.execute(
            select(ColumnModel).where(ColumnModel.table_id.in_(table_ids), ColumnModel.deleted_at.is_(None))
        )
        columns = columns_result.scalars().all()
        
        # Mapping column internal id to public id for foreign key resolution
        column_id_to_public = {c.id: c.public_id for c in columns}

        # 4. Fetch all active indexes for these tables
        indexes_result = await db.execute(
            select(Index).where(Index.table_id.in_(table_ids), Index.deleted_at.is_(None))
        )
        indexes = indexes_result.scalars().all()
        index_ids = [i.id for i in indexes]

        # 5. Fetch all index columns to know which columns belong to which index
        index_columns_result = await db.execute(
            select(IndexColumn).where(IndexColumn.index_id.in_(index_ids))
        )
        index_columns = index_columns_result.scalars().all()

        # Group index columns by index_id
        index_cols_map = {}
        for ic in index_columns:
            index_cols_map.setdefault(ic.index_id, []).append(ic)

        # Mapping column internal id to name for index columns
        column_id_to_name = {c.id: c.name for c in columns}

        # Build responses
        table_responses = []
        for t in tables:
            # Table columns
            t_columns = []
            for c in columns:
                if c.table_id == t.id:
                    fk_table_pub = table_id_to_public.get(c.fk_table_id) if c.fk_table_id else None
                    fk_col_pub = column_id_to_public.get(c.fk_column_id) if c.fk_column_id else None
                    
                    t_columns.append(SchemaColumnResponse(
                        public_id=c.public_id,
                        name=c.name,
                        description=c.description,
                        data_type=c.data_type,
                        is_nullable=c.is_nullable,
                        default_value=c.default_value,
                        is_unique=c.is_unique,
                        ordinal_position=c.ordinal_position,
                        fk_table_public_id=fk_table_pub,
                        fk_column_public_id=fk_col_pub
                    ))
            
            # Table indexes
            t_indexes = []
            for i in indexes:
                if i.table_id == t.id:
                    # Get column names for this index, sorted by ordinal_position
                    idx_cols = index_cols_map.get(i.id, [])
                    idx_cols.sort(key=lambda x: x.ordinal_position)
                    col_names = [column_id_to_name.get(ic.column_id, "unknown") for ic in idx_cols]
                    
                    t_indexes.append(SchemaIndexResponse(
                        public_id=i.public_id,
                        name=i.name,
                        type=i.type,
                        definition=i.definition,
                        is_unique=i.is_unique,
                        is_primary=i.is_primary,
                        columns=col_names
                    ))
            
            table_responses.append(SchemaTableResponse(
                public_id=t.public_id,
                schema_name=t.schema_name,
                name=t.name,
                description=t.description,
                columns=t_columns,
                indexes=t_indexes
            ))

        return SchemaResponse(
            database_public_id=database.public_id,
            tables=table_responses
        )
    except DatabaseNotFoundError:
        raise
    except Exception as e:
        raise SchemaFetchError(str(e))
