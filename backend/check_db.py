import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_db(db_name):
    url = f'postgresql+psycopg://mausam:mausam_dev_password@localhost:5433/{db_name}'
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        res = await conn.execute(text('SELECT version_num FROM alembic_version'))
        print(f'{db_name} Alembic Version:', res.scalar())

        # Check weather_observations schema
        res = await conn.execute(text(
            '''
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'weather_observations';
            '''
        ))
        columns = res.fetchall()
        print(f'{db_name} weather_observations columns:')
        for col in columns:
            print(col)

        # Check PostGIS geometry type
        res = await conn.execute(text(
            '''
            SELECT f_geometry_column, coord_dimension, srid, type 
            FROM geometry_columns 
            WHERE f_table_name = 'weather_observations';
            '''
        ))
        print(f'{db_name} PostGIS columns:', res.fetchall())
        
        # Check Indexes and Constraints
        res = await conn.execute(text(
            '''
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'weather_observations';
            '''
        ))
        indexes = res.fetchall()
        print(f'{db_name} Indexes/Constraints:')
        for idx in indexes:
            print(idx)
            
        # Count rows
        res = await conn.execute(text('SELECT count(*) FROM weather_observations;'))
        print(f'{db_name} weather_observations row count:', res.scalar())

    await engine.dispose()

import sys

async def main():
    try:
        await check_db('mausam_mitra')
    except Exception as e:
        print('mausam_mitra ERROR:', e)
        
    try:
        await check_db('mausam_mitra_test')
    except Exception as e:
        print('mausam_mitra_test ERROR:', e)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
